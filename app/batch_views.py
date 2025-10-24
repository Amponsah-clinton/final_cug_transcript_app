from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import (
    TranscriptRequest, TranscriptStatus, StaffProfile, StudentProfile,
    TranscriptBatch, TranscriptSelection, TranscriptReview
)
from .forms import TranscriptBatchForm, TranscriptSelectionForm, TranscriptReviewForm
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import uuid
from django.db.models import Count


@login_required
@staff_member_required
def select_transcripts_for_batch(request):
    """Exams office selects transcripts to send to registrar"""
    staff = StaffProfile.objects.filter(user=request.user, role='exams_office').first()
    if not staff:
        messages.error(request, "Only Exams Office staff can select transcripts.")
        return redirect('staff_dashboard')
    
 
    available_transcripts = (
        TranscriptRequest.objects.filter(
            payment_made=True,
            selections__isnull=True,
            transcript_type='official'
        )
        .exclude(statuses__stage__in=['approved', 'dispatched'])
        .distinct()
        .select_related('student', 'student__program', 'student__department')
    )
    
    if request.method == 'POST':
        form = TranscriptSelectionForm(request.POST, available_requests=available_transcripts)
        batch_form = TranscriptBatchForm(request.POST)
        
        if form.is_valid() and batch_form.is_valid():
            batch = batch_form.save(commit=False)
            batch.batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
            batch.created_by = staff
            batch.save()
            
            selected_requests = form.cleaned_data['transcript_requests']
            for request_obj in selected_requests:
                TranscriptSelection.objects.create(
                    batch=batch,
                    transcript_request=request_obj
                )
            
            batch.status = 'pending'
            batch.save()

            for request_obj in selected_requests:
                TranscriptStatus.objects.create(
                    transcript_request=request_obj,
                    stage='registrar',
                    updated_by=staff.user.get_full_name() or staff.user.username,
                    remarks='Forwarded to Registrar for final approval.'
                )
                try:
                    recipient = None
                    student = request_obj.student
                    if getattr(student, 'user', None) and getattr(student.user, 'email', None):
                        recipient = student.user.email
                    else:
                        sp = StudentProfile.objects.select_related('user').filter(student=student).first()
                        if sp and getattr(sp.user, 'email', None):
                            recipient = sp.user.email
                    if recipient:
                        subject = "Transcript Forwarded to Registrar"
                        body = (
                            f"Dear {student.name},\n\n"
                            f"Your official transcript has been forwarded to the Registrar for final approval.\n\n"
                            f"Reference: {request_obj.reference_code}\n\n"
                            f"You will receive another email once processing is complete.\n\n"
                            f"Best regards,\n"
                            f"Academic Records Office"
                        )
                        msg = EmailMultiAlternatives(subject=body.split('\n',1)[0], body=body, from_email=settings.EMAIL_HOST_USER, to=[recipient])
                        msg.send(fail_silently=True)
                except Exception as e:
                    print(f"Email (forwarded to registrar) failed: {e}")
            
            messages.success(request, f"Batch {batch.batch_id} created with {selected_requests.count()} transcripts.")
            return redirect('batch_list')
    else:
        form = TranscriptSelectionForm(available_requests=available_transcripts)
        batch_form = TranscriptBatchForm()
    
    return render(request, 'select_transcripts.html', {
        'form': form,
        'batch_form': batch_form,
        'available_transcripts': available_transcripts
    })


@login_required
@staff_member_required
def batch_list(request):
    """List all transcript batches"""
    staff = StaffProfile.objects.filter(user=request.user).first()
    if not staff:
        messages.error(request, "Access denied.")
        return redirect('staff_dashboard')
    
    if staff.role == 'exams_office':
        batches = TranscriptBatch.objects.filter(created_by=staff).order_by('-created_at')
    elif staff.role == 'registrar':
        batches = TranscriptBatch.objects.all().annotate(selection_count=Count('selections')).order_by('-created_at')
    else:
        batches = TranscriptBatch.objects.none()
    
    return render(request, 'batch_list.html', {'batches': batches})


@login_required
@staff_member_required
def review_batch(request, batch_id):
    """Registrar reviews and approves transcript batch"""
    staff = StaffProfile.objects.filter(user=request.user, role='registrar').first()
    if not staff:
        messages.error(request, "Only Registrar can review batches.")
        return redirect('staff_dashboard')
    
    batch = get_object_or_404(TranscriptBatch, batch_id=batch_id)
    selections = list(batch.selections.all().select_related('transcript_request__student'))
    for sel in selections:
        try:
            tr = sel.transcript_request
            sel.is_approved = tr.statuses.filter(stage='approved').exists()
            sel.is_rejected = tr.statuses.filter(stage='rejected').exists()
        except Exception:
            sel.is_approved = False
            sel.is_rejected = False
    
    if request.method == 'POST':
        action = request.POST.get('action')
        selection_id = request.POST.get('selection_id')
        comments = request.POST.get('comments', '')

        if not selection_id:
            messages.error(request, 'Batch-level actions are disabled. Use per-item Approve/Reject controls.')
            return redirect('review_batch', batch_id=batch.batch_id)

        if action in ('approve_one', 'reject_one', 'reapprove_one'):
            selection = batch.selections.filter(id=selection_id).select_related('transcript_request__student').first()
            if not selection:
                messages.error(request, 'Selection not found.')
                return redirect('review_batch', batch_id=batch.batch_id)
            tr = selection.transcript_request
            student = tr.student
            if action in ('approve_one', 'reapprove_one'):
                try:
                    from .utils import generate_official_transcript_pdf
                    transcript_obj, pdf_bytes = generate_official_transcript_pdf(tr, include_registrar=True, include_vc=True, base_url=request.build_absolute_uri('/')[:-1])
                except Exception as e:
                    transcript_obj = None
                    pdf_bytes = None
                    print(f"Failed to generate official PDF: {e}")

                TranscriptStatus.objects.create(
                    transcript_request=tr,
                    stage='approved',
                    updated_by=staff.user.get_full_name(),
                    remarks=comments or 'Approved by Registrar (individual)'
                )
                try:
                    recipient = None
                    if getattr(student, 'user', None) and getattr(student.user, 'email', None):
                        recipient = student.user.email
                    else:
                        sp = StudentProfile.objects.select_related('user').filter(student=student).first()
                        if sp and getattr(sp.user, 'email', None):
                            recipient = sp.user.email
                    if recipient:
                        subject = 'Your Official Transcript is Ready'
                        body = (f"Dear {student.name},\n\nYour official transcript (Reference: {tr.reference_code}) has been approved by the Registrar. The signed PDF is attached.\n\nBest regards,\nAcademic Records Office")
                        from django.core.mail import EmailMultiAlternatives
                        msg = EmailMultiAlternatives(subject=subject, body=body, from_email=settings.EMAIL_HOST_USER, to=[recipient])
                        if pdf_bytes:
                            safe_name = student.name.replace(' ', '_').replace('/', '_')
                            filename = f"{safe_name}_Official_Transcript.pdf"
                            msg.attach(filename, pdf_bytes, 'application/pdf')
                        msg.send(fail_silently=True)
                except Exception as e:
                    print(f"Email notify approve_one failed: {e}")
                messages.success(request, f"Approved {student.name}.")
            elif action == 'reject_one':
                # allow uploading an attachment for the rejection
                attach = request.FILES.get('attachment') if request.FILES else None
                TranscriptStatus.objects.create(
                    transcript_request=tr,
                    stage='rejected',
                    updated_by=staff.user.get_full_name(),
                    remarks=comments or 'Rejected by Registrar (individual)',
                    attachment=attach
                )
                try:
                    recipient = None
                    if getattr(student, 'user', None) and getattr(student.user, 'email', None):
                        recipient = student.user.email
                    else:
                        sp = StudentProfile.objects.select_related('user').filter(student=student).first()
                        if sp and getattr(sp.user, 'email', None):
                            recipient = sp.user.email
                    if recipient:
                        subject = 'Your Transcript Has Been Rejected'
                        body = (f"Dear {student.name},\n\nYour transcript (Reference: {tr.reference_code}) has been rejected by the Registrar.\nRemarks: {comments or 'No remarks provided.'}\n\nBest regards,\nAcademic Records Office")
                        from django.core.mail import EmailMultiAlternatives
                        EmailMultiAlternatives(subject=subject, body=body, from_email=settings.EMAIL_HOST_USER, to=[recipient]).send(fail_silently=True)
                except Exception as e:
                    print(f"Email notify reject_one failed: {e}")
                messages.warning(request, f"Rejected {student.name}.")

            return redirect('review_batch', batch_id=batch.batch_id)
    else:
        form = TranscriptReviewForm()
    
    return render(request, 'review_batch.html', {
        'batch': batch,
        'selections': selections,
        'form': form
    })


@login_required
def student_approved_transcripts(request):
    """Show approved transcripts on student dashboard"""
    profile = StudentProfile.objects.select_related('student').filter(user=request.user).first()
    if not profile or not profile.student:
        messages.error(request, "No student profile found.")
        return redirect('student_dashboard')
    
    approved_transcripts = TranscriptRequest.objects.filter(
        student=profile.student,
        statuses__stage='approved'
    ).distinct().order_by('-date_requested')
    
    return render(request, 'student_approved_transcripts.html', {
        'approved_transcripts': approved_transcripts
    })


@login_required
@staff_member_required
def generate_transcript_preview(request, pk):
    """Generate transcript PDF for preview (registrar use)"""
    from django.http import FileResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from django.contrib.staticfiles import finders
    from io import BytesIO
    import os
    from reportlab.graphics.barcode import code128
    transcript_request = get_object_or_404(TranscriptRequest, pk=pk)
    transcript_obj = getattr(transcript_request, 'transcript', None)
    registrar_obj = None
    
    staff = StaffProfile.objects.filter(user=request.user).first()
    if not staff or staff.role not in ('registrar', 'exams_office'):
        return redirect('staff_dashboard')
    
    transcript_request = get_object_or_404(TranscriptRequest, pk=pk)
    transcript_obj = getattr(transcript_request, 'transcript', None)
    registrar_obj = None
    
    # For unofficial transcripts, use the selected faculty registrar
    if transcript_request.transcript_type == 'unofficial':
        registrar_obj = transcript_request.selected_faculty_registrar
    
    # Fallback to URL parameter or status remarks if no faculty selected
    if not registrar_obj:
        try:
            reg_id = request.GET.get('registrar_id')
            if reg_id:
                from .models import FacultyRegistrar
                registrar_obj = FacultyRegistrar.objects.filter(id=int(reg_id)).first()
        except Exception:
            registrar_obj = None
    
    if not registrar_obj:
        try:
            import re
            st = transcript_request.statuses.filter(stage='exams_office').first()
            if st and st.remarks:
                m = re.search(r'Registrar used:\s*(.+)', st.remarks)
                if m:
                    reg_name = m.group(1).strip()
                    from .models import FacultyRegistrar
                    registrar_obj = FacultyRegistrar.objects.filter(name__iexact=reg_name).first()
        except Exception:
            registrar_obj = None
    
    # If a saved Transcript PDF exists, serve that exact file so preview and download match
    if transcript_obj and getattr(transcript_obj, 'file', None):
        try:
            file_path = transcript_obj.file.path
            # Return the saved PDF directly
            return FileResponse(open(file_path, 'rb'), as_attachment=False, filename=f"Transcript_Preview_{transcript_request.student.index_number}.pdf")
        except Exception:
            # Fall back to generating on-the-fly below
            pass
    transcript_request = get_object_or_404(TranscriptRequest, pk=pk)
    transcript_obj = getattr(transcript_request, 'transcript', None)
    registrar_obj = None

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    student = transcript_request.student

    def draw_page_content():
        if transcript_request.transcript_type == 'unofficial':
            p.setFont("Helvetica-Bold", 18)
            p.drawCentredString(width / 2, height - 80, "Unofficial Transcript")
        else:
            p.setFont("Helvetica-Bold", 18)
            p.drawCentredString(width / 2, height - 80, "OFFICIAL TRANSCRIPT")

        p.setFont("Helvetica", 12)
        y = height - 140
        details = [
            f"Name: {student.name}",
            f"Index Number: {student.index_number}",
            f"Program: {student.program.name}",
            f"Department: {student.department.department}",
            f"Transcript Type: {transcript_request.get_transcript_type_display()}",
            f"Reference Code: {transcript_request.reference_code}",
            f"Date Requested: {transcript_request.date_requested.strftime('%Y-%m-%d %H:%M')}",
        ]
        for line in details:
            p.drawString(100, y, line)
            y -= 20

        p.line(80, y - 10, width - 80, y - 10)

        sig_y = 120
        sig_w = 180
        sig_h = 60
        center_x = width / 2
        sig_x = center_x - (sig_w / 2)

        if transcript_request.transcript_type == 'unofficial':
            try:
                if registrar_obj and getattr(registrar_obj, 'signature', None):
                    storage = getattr(registrar_obj.signature, 'storage', None)
                    sig_name = getattr(registrar_obj.signature, 'name', None)
                    sig_bytes = None
                    # Try storage first
                    if storage and sig_name:
                        try:
                            with storage.open(sig_name, 'rb') as fh:
                                sig_bytes = fh.read()
                        except Exception:
                            sig_bytes = None

                    # Try media registrar_signatures folder
                    if not sig_bytes:
                        try:
                            media_path = os.path.join('media', 'registrar_signatures', os.path.basename(getattr(registrar_obj.signature, 'name', '') or ''))
                            if os.path.exists(media_path):
                                with open(media_path, 'rb') as fh:
                                    sig_bytes = fh.read()
                        except Exception:
                            sig_bytes = None

                    # Try app images as final fallback
                    if not sig_bytes:
                        try:
                            local_path = os.path.join(os.path.dirname(__file__), 'images', 'registrar.jpg')
                            if os.path.exists(local_path):
                                with open(local_path, 'rb') as fh:
                                    sig_bytes = fh.read()
                        except Exception:
                            sig_bytes = None

                    if sig_bytes:
                        from reportlab.lib.utils import ImageReader
                        img = ImageReader(BytesIO(sig_bytes))
                        p.drawImage(img, sig_x, sig_y, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                        p.setFont("Helvetica-Bold", 10)
                        p.drawCentredString(center_x, sig_y - 14, registrar_obj.name)
                        p.setFont("Helvetica", 9)
                        faculty_label = getattr(registrar_obj, 'faculty_name', '')
                        if faculty_label:
                            p.drawCentredString(center_x, sig_y - 28, f"{faculty_label} (Registrar)")
                        else:
                            p.drawCentredString(center_x, sig_y - 28, "(Registrar)")
                    else:
                        p.setFont("Helvetica", 10)
                        if registrar_obj:
                            p.drawCentredString(center_x, sig_y + sig_h / 2 - 6, f"{registrar_obj.name} - {getattr(registrar_obj, 'faculty_name', '')} (Registrar)")
                        else:
                            p.drawCentredString(center_x, sig_y + sig_h / 2 - 6, "Registrar (not selected)")
            except Exception:
                pass
        else:
            x_positions = [180, 360]
            try:
                # Prefer StaffProfile entries for Registrar and Vice Chancellor
                from .models import StaffProfile
                from .utils import load_signature_image

                reg_profile = StaffProfile.objects.filter(role='registrar').select_related('user').first()
                vc_profile = StaffProfile.objects.filter(role='vice_chancellor').select_related('user').first()

                # Registrar
                try:
                    reg_img_reader = None
                    # Prefer uploaded signature field
                    if reg_profile and getattr(reg_profile, 'signature', None):
                        reg_img_reader = load_signature_image(reg_profile.signature)

                    # static fallback
                    if not reg_img_reader:
                        reg_path = finders.find('images/registrar.jpg') or os.path.join(os.path.dirname(__file__), 'images', 'registrar.jpg')
                        if reg_path:
                            reg_img_reader = load_signature_image(reg_path)

                    if reg_img_reader:
                        p.drawImage(reg_img_reader, x_positions[0], sig_y, width=120, height=60, preserveAspectRatio=True, mask='auto')

                    p.setFont("Helvetica-Bold", 10)
                    reg_name = (reg_profile.user.get_full_name() if getattr(reg_profile, 'user', None) else None) or (reg_profile.user.username if getattr(reg_profile, 'user', None) else (reg_profile.staff_id if reg_profile else 'Registrar'))
                    p.drawCentredString(x_positions[0] + 60, sig_y - 16, reg_name)
                    p.setFont("Helvetica", 9)
                    p.drawCentredString(x_positions[0] + 60, sig_y - 30, 'Registrar')
                except Exception:
                    pass

                # Vice Chancellor
                try:
                    vc_img_reader = None
                    # Prefer uploaded signature field
                    if vc_profile and getattr(vc_profile, 'signature', None):
                        vc_img_reader = load_signature_image(vc_profile.signature)

                    if not vc_img_reader:
                        vc_path = finders.find('images/vice_chancellor.png') or os.path.join(os.path.dirname(__file__), 'images', 'vice_chancellor.png')
                        if vc_path:
                            vc_img_reader = load_signature_image(vc_path)

                    if vc_img_reader:
                        p.drawImage(vc_img_reader, x_positions[1], sig_y, width=120, height=60, preserveAspectRatio=True, mask='auto')

                    p.setFont("Helvetica-Bold", 10)
                    vc_name = (vc_profile.user.get_full_name() if getattr(vc_profile, 'user', None) else None) or (vc_profile.user.username if getattr(vc_profile, 'user', None) else 'Vice Chancellor')
                    p.drawCentredString(x_positions[1] + 60, sig_y - 16, vc_name)
                    p.setFont("Helvetica", 9)
                    p.drawCentredString(x_positions[1] + 60, sig_y - 30, 'Vice Chancellor')
                except Exception:
                    pass
            except Exception:
                # last-resort fallback to static images/names
                reg_img = finders.find('images/registrar.jpg')
                vc_img = finders.find('images/vice_chancellor.png')
                try:
                    if reg_img and os.path.exists(reg_img):
                        p.drawImage(reg_img, x_positions[0], sig_y, width=120, height=60, preserveAspectRatio=True, mask='auto')
                    p.setFont("Helvetica-Bold", 10)
                    p.drawCentredString(x_positions[0] + 60, sig_y - 16, 'Registrar')
                    p.setFont("Helvetica", 9)
                    p.drawCentredString(x_positions[0] + 60, sig_y - 30, 'Registrar')
                except Exception:
                    pass
                try:
                    if vc_img and os.path.exists(vc_img):
                        p.drawImage(vc_img, x_positions[1], sig_y, width=120, height=60, preserveAspectRatio=True, mask='auto')
                    p.setFont("Helvetica-Bold", 10)
                    p.drawCentredString(x_positions[1] + 60, sig_y - 16, 'Vice Chancellor')
                    p.setFont("Helvetica", 9)
                    p.drawCentredString(x_positions[1] + 60, sig_y - 30, 'Vice Chancellor')
                except Exception:
                    pass

        try:
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics.barcode.qr import QrCodeWidget
            try:
                import re
                ref = transcript_request.reference_code or ''
                ref_clean = re.sub(r'(?i)^ref[-_]?','', ref)
                index = getattr(student, 'index_number', '')
                code = f"{index}{ref_clean}"
                base_url = request.build_absolute_uri('/')[:-1]
                import urllib.parse
                encoded = urllib.parse.quote(code)
                qr_payload = f"{base_url}/verify/{encoded}/"

                # Centered QR in middle of page
                qr_size = 140
                qr_x = (width - qr_size) / 2
                qr_y = (height / 2) - (qr_size / 2) - 20
                qr = QrCodeWidget(qr_payload)
                d = Drawing(qr_size, qr_size)
                d.add(qr)
                from reportlab.graphics import renderPDF
                renderPDF.draw(d, p, qr_x, qr_y)

                # Centered verification instructions under the QR
                try:
                    manual_link = f"{base_url}/verify/{encoded}/"
                except Exception:
                    manual_link = f"{base_url}/verify/"

                p.setFont("Helvetica-Bold", 10)
                p.drawCentredString(width / 2, qr_y - 10, "Scan the QR code above to verify this transcript.")
                p.setFont("Helvetica", 9)
                p.drawCentredString(width / 2, qr_y - 26, f"Or visit: {manual_link}")
                p.drawCentredString(width / 2, qr_y - 40, f"You can also verify manually using the Reference Code: {manual_link}")
            except Exception:
                pass
        except Exception:
            pass

    draw_page_content()
    p.showPage()
    p.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    # Note: This is a preview function - we do NOT save to Transcript model
    # to avoid moving the request to "processed" status

    return FileResponse(BytesIO(pdf_bytes), as_attachment=False, filename=f"Transcript_Preview_{student.index_number}.pdf")


@login_required
@staff_member_required
def update_transcript_signatures(request, pk):
    """Registrar can GET current flags or POST updates to signature flags for a transcript request."""
    from django.http import JsonResponse

    staff = StaffProfile.objects.filter(user=request.user, role='registrar').first()
    if not staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    transcript_request = get_object_or_404(TranscriptRequest, pk=pk)
    from .models import Transcript
    transcript_obj, _ = Transcript.objects.get_or_create(transcript_request=transcript_request)

    if request.method == 'GET':
        return JsonResponse({
            'hod': bool(transcript_obj.dean_signature),
            'registrar': bool(transcript_obj.registrar_signature),
            'vc': bool(transcript_obj.vc_signature),
        })

    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        transcript_obj.dean_signature = bool(data.get('hod'))
        transcript_obj.registrar_signature = bool(data.get('registrar'))
        transcript_obj.vc_signature = bool(data.get('vc'))
        transcript_obj.save(update_fields=['dean_signature', 'registrar_signature', 'vc_signature'])

        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
