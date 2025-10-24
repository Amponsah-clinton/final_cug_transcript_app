

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from .models import Transcript
from django.utils import timezone
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128
from django.contrib.staticfiles import finders
import urllib.parse
import os

from reportlab.lib.utils import ImageReader
from io import BytesIO
try:
    from PIL import Image
except Exception:
    Image = None

# For merging PDFs
try:
    import PyPDF2
except Exception:
    PyPDF2 = None


def load_signature_image(field_or_path):
    """
    Accepts an ImageField-like object or a filesystem path.
    Returns a ReportLab ImageReader or None.
    Tries storage.open for fields, then treats strings as file paths.
    """
    try:
        # If it's an ImageField/FileField instance
        storage = getattr(field_or_path, 'storage', None)
        name = getattr(field_or_path, 'name', None)
        if storage and name:
            try:
                with storage.open(name, 'rb') as fh:
                    data = fh.read()
                    # Optionally normalize using PIL to ensure compatibility
                    if Image:
                        try:
                            img = Image.open(BytesIO(data))
                            if img.mode in ('RGBA', 'P'):
                                img = img.convert('RGB')
                            out = BytesIO()
                            img.save(out, format='PNG')
                            out.seek(0)
                            return ImageReader(out)
                        except Exception:
                            return ImageReader(BytesIO(data))
                    return ImageReader(BytesIO(data))
            except Exception:
                return None

        # If it's a string path
        if isinstance(field_or_path, str):
            if os.path.exists(field_or_path):
                try:
                    # Use PIL normalization when available
                    if Image:
                        img = Image.open(field_or_path)
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        out = BytesIO()
                        img.save(out, format='PNG')
                        out.seek(0)
                        return ImageReader(out)
                    return ImageReader(field_or_path)
                except Exception:
                    return None

    except Exception:
        return None
    return None


def send_sms(to, message):
    try:
        # If Twilio client isn't configured in this environment, skip sending gracefully
        client_obj = globals().get('client')
        twilio_from = globals().get('TWILIO_PHONE_NUMBER')
        if not client_obj or not twilio_from:
            return False, 'Twilio not configured'
        message = client_obj.messages.create(
            body=message,
            from_=twilio_from,
            to=to
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)


from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from .models import Transcript
import urllib


def generate_unofficial_transcript_pdf(transcript_request, faculty_registrar, base_url=None):
    """
    Generate an Unofficial Transcript with Faculty Registrar's permanent signature and name.
    The file is saved in Transcript.file and is viewable by Registrar as-is.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # === Header ===
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 80, "Unofficial Transcript")

    y = height - 140
    student = transcript_request.student
    details = [
        f"Name: {student.name}",
        f"Index Number: {student.index_number}",
        f"Program: {getattr(student.program, 'name', '')}",
        f"Department: {getattr(student.department, 'department', '')}",
        f"Transcript Type: {transcript_request.get_transcript_type_display()}",
        f"Reference Code: {transcript_request.reference_code}",
        f"Date Requested: {transcript_request.date_requested.strftime('%Y-%m-%d %H:%M')}",
    ]
    for line in details:
        p.drawString(100, y, line)
        y -= 20

    p.line(80, y - 10, width - 80, y - 10)
    y -= 60

    # === Footer ===
    def draw_footer(canvas_obj):
        try:
            footer_margin = 40
            sig_w, sig_h = 180, 60
            page_width, page_height = A4

            # Centered QR block in the middle of the page
            qr_size = 140
            qr_x = (page_width - qr_size) / 2
            qr_y = (page_height / 2) - (qr_size / 2) - 20

            center_x = page_width / 2
            sig_x = center_x - (sig_w / 2)
            sig_y = footer_margin

            # === Faculty Registrar Signature Block ===
            if faculty_registrar:
                try:
                    img_reader = None
                    # Prefer the FacultyRegistrar.signature field when available
                    if getattr(faculty_registrar, 'signature', None):
                        try:
                            img_reader = load_signature_image(faculty_registrar.signature)
                        except Exception:
                            img_reader = None

                    # Fallback to local app images folder
                    if not img_reader:
                        try:
                            local_sig = os.path.join(os.path.dirname(__file__), 'images', 'registrar.jpg')
                            if os.path.exists(local_sig):
                                img_reader = load_signature_image(local_sig)
                        except Exception:
                            img_reader = None

                    if img_reader:
                        canvas_obj.drawImage(img_reader, sig_x, sig_y,
                                             width=sig_w, height=sig_h,
                                             preserveAspectRatio=True, mask='auto')
                except Exception as e:
                    print(f"Signature render failed: {e}")

                # Always write Faculty Registrar name + faculty name
                canvas_obj.setFont("Helvetica-Bold", 10)
                canvas_obj.drawCentredString(center_x, sig_y - 14, faculty_registrar.name)
                canvas_obj.setFont("Helvetica", 9)
                faculty_label = getattr(faculty_registrar, 'faculty_name', '')
                label = f"{faculty_label} (Faculty Registrar)" if faculty_label else "(Faculty Registrar)"
                canvas_obj.drawCentredString(center_x, sig_y - 28, label)
            else:
                # Show message if no faculty registrar selected
                canvas_obj.setFont("Helvetica", 10)
                canvas_obj.drawCentredString(center_x, sig_y + sig_h / 2 - 6, "Faculty Registrar (not selected)")

            # === QR Code ===
            try:
                student = transcript_request.student
                index = getattr(student, 'index_number', '')
                ref = transcript_request.reference_code or ''
                import re
                ref_clean = re.sub(r'(?i)^ref[-_]?','', ref)
                code = f"{index}{ref_clean}"
                if base_url:
                    encoded = urllib.parse.quote(code)
                    qr_payload = f"{base_url.rstrip('/')}/verify/{encoded}/"
                    manual_link = f"{base_url.rstrip('/')}/verify/{encoded}/"
                else:
                    qr_payload = code
                    manual_link = code

                qr = QrCodeWidget(qr_payload)
                d = Drawing(qr_size, qr_size)
                d.add(qr)
                renderPDF.draw(d, canvas_obj, qr_x, qr_y)
            except Exception:
                manual_link = f"{base_url.rstrip('/')}/verify/" if base_url else "/verify/"

            # === Verification Instructions (centered under QR) ===
            try:
                canvas_obj.setFont("Helvetica-Bold", 10)
                canvas_obj.drawCentredString(page_width / 2, qr_y - 10, "Scan the QR code above to verify this transcript.")
                canvas_obj.setFont("Helvetica", 9)
                canvas_obj.drawCentredString(page_width / 2, qr_y - 26, f"Or visit: {manual_link}")
                canvas_obj.drawCentredString(page_width / 2, qr_y - 40, "You can also verify manually using the Reference Code: http://127.0.0.1:8000/manual/verify/")
            except Exception:
                pass
            
            # === Note ===
            canvas_obj.setFont("Helvetica-Oblique", 9)
            canvas_obj.drawString(60, footer_margin - 10, "Unofficial Transcript - Not for official use")

        except Exception as e:
            print(f"Footer drawing failed: {e}")

    draw_footer(p)
    p.showPage()
    p.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    transcript_obj, _ = Transcript.objects.get_or_create(transcript_request=transcript_request)
    transcript_obj.generated_by = getattr(transcript_request.student, 'name', 'System')
    transcript_obj.date_generated = timezone.now()
    try:
        transcript_obj.registrar_signature = bool(faculty_registrar)
    except Exception:
        pass
    transcript_obj.file.save(
        f"{transcript_request.reference_code}_unofficial.pdf",
        ContentFile(pdf_bytes),
        save=True
    )

    # If registrar uploaded an original PDF, append it as following pages
    try:
        if PyPDF2 and getattr(transcript_obj, 'uploaded_file', None):
            uploaded_field = transcript_obj.uploaded_file
            storage = getattr(uploaded_field, 'storage', None)
            name = getattr(uploaded_field, 'name', None)
            if storage and name:
                with storage.open(name, 'rb') as fh:
                    uploaded_bytes = fh.read()
                    # Merge using PyPDF2
                    output = PyPDF2.PdfWriter()
                    # read generated
                    gen_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
                    for p in gen_reader.pages:
                        output.add_page(p)
                    try:
                        up_reader = PyPDF2.PdfReader(BytesIO(uploaded_bytes))
                        for p in up_reader.pages:
                            output.add_page(p)
                    except Exception:
                        # If uploaded file isn't a valid PDF, skip appending
                        pass
                    out_buf = BytesIO()
                    output.write(out_buf)
                    out_bytes = out_buf.getvalue()
                    transcript_obj.file.save(
                        f"{transcript_request.reference_code}_unofficial_combined.pdf",
                        ContentFile(out_bytes),
                        save=True
                    )
                    pdf_bytes = out_bytes
    except Exception:
        pass

    return transcript_obj, pdf_bytes


def generate_official_transcript_pdf(transcript_request, include_registrar=True, include_vc=True, base_url=None):
    from reportlab.lib.utils import ImageReader
    from .models import StaffProfile

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # === Header ===
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 80, "OFFICIAL TRANSCRIPT")

    # === Student Details ===
    y = height - 140
    student = transcript_request.student
    details = [
        f"Name: {student.name}",
        f"Index Number: {student.index_number}",
        f"Program: {getattr(student.program, 'name', '')}",
        f"Department: {getattr(student.department, 'department', '')}",
        f"Transcript Type: {transcript_request.get_transcript_type_display()}",
        f"Reference Code: {transcript_request.reference_code}",
        f"Date Requested: {transcript_request.date_requested.strftime('%Y-%m-%d %H:%M')}",
    ]
    p.setFont("Helvetica", 11)
    for line in details:
        p.drawString(100, y, line)
        y -= 18

    p.line(80, y - 10, width - 80, y - 10)

    # === We'll render a centered verification block (QR + instructions) in the middle of page
    qr_size = 140
    qr_x = (width - qr_size) / 2
    qr_y = (height / 2) - (qr_size / 2) - 20

    # Signatures area (footer) - reserve a band above page bottom
    sig_w, sig_h = 160, 60
    footer_sig_y = 80
    mid_x = width / 2

    # Registrar signature (footer-left)
    if include_registrar:
        try:
            # Prefer StaffProfile (site registrar) for name/signature
            reg_profile = StaffProfile.objects.filter(role='registrar').select_related('user').first()
            drawn = False
            if reg_profile and getattr(reg_profile, 'signature', None):
                try:
                    sig_field = reg_profile.signature
                    storage = getattr(sig_field, 'storage', None)
                    sig_name = getattr(sig_field, 'name', None)
                    if storage and sig_name:
                        with storage.open(sig_name, 'rb') as fh:
                            img = ImageReader(BytesIO(fh.read()))
                            p.drawImage(img, mid_x - sig_w - 20, footer_sig_y, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                            drawn = True
                except Exception as e:
                    print(f"Registrar signature (profile) render failed: {e}")

            if not drawn:
                # Try static finders then local app images folder using loader
                reg_path = finders.find('images/registrar.jpg') or os.path.join(os.path.dirname(__file__), 'images', 'registrar.jpg')
                if reg_path:
                    try:
                        img = load_signature_image(reg_path)
                        if img:
                            p.drawImage(img, mid_x - sig_w - 20, footer_sig_y, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                            drawn = True
                    except Exception as e:
                        print(f"Registrar signature (static) render failed: {e}")

            p.setFont('Helvetica-Bold', 10)
            # Name: prefer StaffProfile.user.get_full_name(), then username, then staff_id, then 'Registrar'
            reg_name = 'Registrar'
            try:
                if reg_profile and getattr(reg_profile, 'user', None):
                    reg_name = reg_profile.user.get_full_name() or reg_profile.user.username or getattr(reg_profile, 'staff_id', 'Registrar')
                elif reg_profile:
                    reg_name = getattr(reg_profile, 'staff_id', 'Registrar')
            except Exception:
                reg_name = 'Registrar'

            p.drawCentredString(mid_x - sig_w - 20 + (sig_w/2), footer_sig_y - 14, reg_name)
            p.setFont('Helvetica', 9)
            p.drawCentredString(mid_x - sig_w - 20 + (sig_w/2), footer_sig_y - 28, 'Registrar')
        except Exception as e:
            print(f"Registrar signature failed: {e}")

    # VC
    if include_vc:
        try:
            # Prefer StaffProfile (site VC) for name/signature
            vc_profile = StaffProfile.objects.filter(role='vice_chancellor').select_related('user').first()
            drawn_vc = False
            if vc_profile and getattr(vc_profile, 'signature', None):
                try:
                    sig_field = vc_profile.signature
                    storage = getattr(sig_field, 'storage', None)
                    sig_name = getattr(sig_field, 'name', None)
                    if storage and sig_name:
                        with storage.open(sig_name, 'rb') as fh:
                            img = ImageReader(BytesIO(fh.read()))
                            p.drawImage(img, mid_x + 20, footer_sig_y, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                            drawn_vc = True
                except Exception as e:
                    print(f"VC signature (profile) render failed: {e}")

            if not drawn_vc:
                vc_path = finders.find('images/vice_chancellor.png') or os.path.join(os.path.dirname(__file__), 'images', 'vice_chancellor.png')
                if vc_path:
                    try:
                        img = load_signature_image(vc_path)
                        if img:
                            p.drawImage(img, mid_x + 20, footer_sig_y, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                            drawn_vc = True
                    except Exception as e:
                        print(f"VC signature (static) render failed: {e}")

            p.setFont('Helvetica-Bold', 10)
            vc_name = 'Vice Chancellor'
            try:
                if vc_profile and getattr(vc_profile, 'user', None):
                    vc_name = vc_profile.user.get_full_name() or vc_profile.user.username or getattr(vc_profile, 'staff_id', 'Vice Chancellor')
                elif vc_profile:
                    vc_name = getattr(vc_profile, 'staff_id', 'Vice Chancellor')
            except Exception:
                vc_name = 'Vice Chancellor'

            p.drawCentredString(mid_x + sig_w + 20 - (sig_w/2), footer_sig_y - 14, vc_name)
            p.setFont('Helvetica', 9)
            p.drawCentredString(mid_x + sig_w + 20 - (sig_w/2), footer_sig_y - 28, 'Vice Chancellor')
        except Exception as e:
            print(f"VC signature failed: {e}")
    # === Centered verification block in the middle of the page ===
    try:
        import re
        ref = transcript_request.reference_code or ''
        ref_clean = re.sub(r'(?i)^ref[-_]?','', ref)
        index = getattr(student, 'index_number', '')
        code = f"{index}{ref_clean}"
        if base_url:
            qr_payload = f"{base_url.rstrip('/')}/verify/{urllib.parse.quote(code)}/"
            manual_link = f"{base_url.rstrip('/')}/verify/{urllib.parse.quote(code)}/"
        else:
            qr_payload = code
            manual_link = code
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics import renderPDF
        qr = QrCodeWidget(qr_payload)
        d = Drawing(qr_size, qr_size)
        d.add(qr)
        renderPDF.draw(d, p, qr_x, qr_y)
    except Exception as e:
        print(f"QR generation failed: {e}")

    # === Verification instructions centered under QR block ===
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(width / 2, qr_y - 10, "Scan the QR code above to verify this transcript.")
    p.setFont("Helvetica", 9)
    try:
        # Display full per-transcript verification link when possible
        if base_url:
            p.drawCentredString(width / 2, qr_y - 26, f"Or visit: {manual_link}")
        else:
            p.drawCentredString(width / 2, qr_y - 26, f"Or verify using code: {code}")
    except Exception:
        # fallback to generic verify page
        p.drawCentredString(width / 2, qr_y - 26, f"Or visit: {base_url}/verify/" if base_url else "/verify/")
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(width / 2, 20, "Official Transcript - Catholic University of Ghana")

    p.showPage()
    p.save()
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    transcript_obj, _ = Transcript.objects.get_or_create(transcript_request=transcript_request)
    transcript_obj.generated_by = transcript_obj.generated_by or 'Registrar'
    transcript_obj.date_generated = timezone.now()
    transcript_obj.registrar_signature = bool(include_registrar)
    transcript_obj.vc_signature = bool(include_vc)
    file_name = f"{transcript_request.reference_code}_Official.pdf"
    transcript_obj.file.save(file_name, ContentFile(pdf_bytes), save=True)

    # If registrar uploaded an original PDF, append it as following pages
    try:
        if PyPDF2 and getattr(transcript_obj, 'uploaded_file', None):
            uploaded_field = transcript_obj.uploaded_file
            storage = getattr(uploaded_field, 'storage', None)
            name = getattr(uploaded_field, 'name', None)
            if storage and name:
                with storage.open(name, 'rb') as fh:
                    uploaded_bytes = fh.read()
                    output = PyPDF2.PdfWriter()
                    gen_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
                    for p in gen_reader.pages:
                        output.add_page(p)
                    try:
                        up_reader = PyPDF2.PdfReader(BytesIO(uploaded_bytes))
                        for p in up_reader.pages:
                            output.add_page(p)
                    except Exception:
                        pass
                    out_buf = BytesIO()
                    output.write(out_buf)
                    out_bytes = out_buf.getvalue()
                    transcript_obj.file.save(
                        f"{transcript_request.reference_code}_Official_combined.pdf",
                        ContentFile(out_bytes),
                        save=True
                    )
                    pdf_bytes = out_bytes
    except Exception:
        pass

    return transcript_obj, pdf_bytes
