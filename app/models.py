from django.db import models
from django.utils import timezone
import uuid


from django.contrib.auth.models import User


class Department(models.Model):
    department = models.CharField(max_length=100)
    HoD = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.department} ({self.HoD})"


class Program(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')

    def __str__(self):
        return f"{self.name} ({self.department.department})"



class TranscriptType(models.Model):
    TYPE_CHOICES = [
        ('official', 'Official Transcript'),
        ('unofficial', 'Unofficial Transcript'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_type_display()} - GHS {self.price}"
    

from django.db import models
from django.contrib.auth.models import User

def get_default_user():
    try:
        return User.objects.first().id   
    except Exception:
        return None

class Student(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    name = models.CharField(max_length=100)
    index_number = models.CharField(max_length=50, unique=True)
    date_entered = models.DateField(null=True, blank=True)
    date_completed = models.DateField(null=True, blank=True)
    program = models.ForeignKey('Program', on_delete=models.CASCADE, related_name='students')
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='students')
    owes_fees = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.program and self.program.department:
            self.department = self.program.department
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.index_number}"
    
    @property
    def full_name(self):
        return self.name  # Simple wrapper for templates expecting "full_name"

    def __str__(self):
        return f"{self.name} - {self.index_number}"






class FacultyRegistrar(models.Model):
    name = models.CharField(max_length=255)
    signature = models.ImageField(upload_to='registrar_signatures/')
    faculty_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.faculty_name}"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, null=True, blank=True)
    index_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.index_number})"

        return f"{self.user.username} ({self.index_number})"
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()



class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('exams_office', 'Exams Office'),
        ('accounts_office', 'Accounts Office'),
        ('hod', 'Head of Department'),
        ('dean_of_student', 'Dean of Student'),
        ('vice_chancellor', 'Vice Chancellor'),
        ('registrar', 'Registrar'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='staff_pics/', blank=True, null=True)
    signature = models.ImageField(upload_to='staff_signatures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"


class TranscriptRequest(models.Model):
    TRANSCRIPT_TYPE_CHOICES = [
        ('official', 'Official Transcript'),
        ('unofficial', 'Unofficial Transcript'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='requests')
    transcript_type = models.CharField(max_length=20, choices=TRANSCRIPT_TYPE_CHOICES, null=True, blank=True)
    date_requested = models.DateTimeField(default=timezone.now)
    reference_code = models.CharField(max_length=100, unique=True)
    payment_made = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=100.00)
    selected_faculty_registrar = models.ForeignKey(
        'FacultyRegistrar',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transcript_requests'
    )
    def __str__(self):
        return f"{self.student.name} - {self.transcript_type or 'Pending Payment'}"


class TranscriptStatus(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cash_office', 'At Cash Office'),
        ('exams_office', 'At Exams Office'),
        ('registrar', 'At Registrar'),
        ('approved', 'Approved'),
        ('dispatched', 'Dispatched'),
        ('rejected', 'Rejected'),
        ('disapproved', 'Disapproved'),
    ]

    transcript_request = models.ForeignKey(TranscriptRequest, on_delete=models.CASCADE, related_name='statuses')
    stage = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    updated_by = models.CharField(max_length=100)
    updated_on = models.DateTimeField(default=timezone.now)
    attachment = models.FileField(upload_to='transcript_status_attachments/', blank=True, null=True)

    class Meta:
        ordering = ['-updated_on']

    def __str__(self):
        return f"{self.transcript_request.student.name} - {self.stage}"


class Payment(models.Model):
    transcript_request = models.OneToOneField(TranscriptRequest, on_delete=models.CASCADE, related_name='payment')
    cleared = models.BooleanField(default=False)
    officer_name = models.CharField(max_length=100)
    date_checked = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    # Breakdown of amounts (allow nulls to remain compatible)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_accounts_office = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_superadmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_registrar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.transcript_request.student.name} - {'Cleared' if self.cleared else 'Uncleared'}"


class Transcript(models.Model):
    transcript_request = models.OneToOneField(TranscriptRequest, on_delete=models.CASCADE, related_name='transcript')
    transcript_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    generated_by = models.CharField(max_length=100)
    date_generated = models.DateTimeField(default=timezone.now)
    dean_signature = models.BooleanField(default=False)
    registrar_signature = models.BooleanField(default=False)
    vc_signature = models.BooleanField(default=False)
    file = models.FileField(upload_to='transcripts/', blank=True, null=True)
    # If registrar uploads an original PDF, keep a copy here
    uploaded_file = models.FileField(upload_to='transcript_uploads/', blank=True, null=True)

    def __str__(self):
        return f"Transcript {self.transcript_id}"


class TranscriptApproval(models.Model):
    transcript = models.OneToOneField(Transcript, on_delete=models.CASCADE, related_name='approval')
    approved = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)  # ✅ allow blank + null
    date_approved = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.transcript.transcript_request.student.name} - {'Approved' if self.approved else 'Pending'}"

class TranscriptApprovalHistory(models.Model):
    """Track all approval/disapproval actions for a transcript"""
    transcript_request = models.ForeignKey(TranscriptRequest, on_delete=models.CASCADE, related_name='approval_history')
    action = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('disapproved', 'Disapproved'),
        ('reapproved', 'Re-approved'),
    ])
    approved_by = models.CharField(max_length=100)
    remarks = models.TextField(blank=True, null=True)
    date_action = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.transcript_request.student.name} - {self.get_action_display()} by {self.approved_by}"


class TranscriptVerification(models.Model):
    transcript = models.OneToOneField(Transcript, on_delete=models.CASCADE, related_name='verification')
    barcode = models.CharField(max_length=100, unique=True)
    verified = models.BooleanField(default=False)
    date_verified = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Verification for {self.transcript.transcript_request.student.name}"

class FeeClearance(models.Model):
    transcript_request = models.OneToOneField(TranscriptRequest, on_delete=models.CASCADE, related_name='fee_clearance')
    cleared = models.BooleanField(default=False)
    owes = models.BooleanField(default=False)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    officer_name = models.CharField(max_length=255)
    invoice_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    date_checked = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fee clearance for {self.transcript_request.reference_code}"



from django.contrib.auth.models import User
from django.db import models



class TranscriptBatch(models.Model):
    """Batch of transcripts selected by exams office for registrar review"""
    STATUS_CHOICES = [
        ('pending', 'Pending Registrar Review'),
        ('under_review', 'Under Registrar Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    batch_id = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='created_batches')
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.get_status_display()}"


class TranscriptSelection(models.Model):
    """Individual transcript selected for batch processing"""
    batch = models.ForeignKey(TranscriptBatch, on_delete=models.CASCADE, related_name='selections')
    transcript_request = models.ForeignKey(TranscriptRequest, on_delete=models.CASCADE, related_name='selections')
    selected_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['batch', 'transcript_request']
    
    def __str__(self):
        return f"{self.transcript_request.student.name} in {self.batch.batch_id}"


class TranscriptReview(models.Model):
    """Registrar's review and approval of transcript batches"""
    batch = models.OneToOneField(TranscriptBatch, on_delete=models.CASCADE, related_name='review')
    reviewed_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewed_at = models.DateTimeField(default=timezone.now)
    approved = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    changes_made = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Review of {self.batch.batch_id} by {self.reviewed_by.user.get_full_name()}"


class PasswordResetCode(models.Model):
    """One-time code for password reset sent to user's email."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_codes')
    code = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        return (not self.used) and (timezone.now() <= self.expires_at)

    def __str__(self):
        return f"PasswordResetCode for {self.user.email} (used={self.used})"



from django.db import models

class WhatsAppGroup(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    link = models.URLField(help_text="Enter the WhatsApp group invite link.")
    icon = models.CharField(max_length=50, default='fa-users', help_text="FontAwesome icon class, e.g., 'fa-users'.")
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']
        verbose_name = "WhatsApp Group"
        verbose_name_plural = "WhatsApp Groups"

    def __str__(self):
        return self.name

from django.db import models

class Contact(models.Model):
    department = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

    def __str__(self):
        return f"{self.department} - {self.phone_number}"

