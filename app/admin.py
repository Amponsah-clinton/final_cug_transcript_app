from django.contrib import admin
from .models import (
    Department,
    Student,
    StudentProfile,
    TranscriptRequest,
    TranscriptStatus,
    Payment,
    Transcript,
    TranscriptApproval,Program,
    TranscriptVerification,
    FacultyRegistrar,TranscriptType
)

from django.contrib import admin
from .models import WhatsAppGroup, Contact


@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_on')
    list_filter = ('active', 'created_on')
    search_fields = ('name', 'description')
    ordering = ('-created_on',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('department', 'phone_number', 'active')
    list_filter = ('active',)
    search_fields = ('department', 'phone_number')

admin.site.register(TranscriptType)

@admin.register(FacultyRegistrar)
class FacultyRegistrarAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty_name')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department', 'HoD')
    search_fields = ('department', 'HoD')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'index_number', 'department', 'date_entered', 'date_completed', 'owes_fees')
    list_filter = ('department', 'owes_fees')
    search_fields = ('name', 'index_number')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'index_number', 'phone_number')
    search_fields = ('user__username', 'index_number', 'phone_number')


@admin.register(TranscriptRequest)
class TranscriptRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'transcript_type', 'date_requested', 'reference_code', 'payment_made')
    list_filter = ('transcript_type', 'payment_made')
    search_fields = ('student__name', 'reference_code')

@admin.register(TranscriptStatus)
class TranscriptStatusAdmin(admin.ModelAdmin):
    list_display = ('transcript_request', 'stage', 'updated_by', 'updated_on')
    list_filter = ('stage',)
    search_fields = ('transcript_request__student__name', 'updated_by')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transcript_request', 'cleared', 'officer_name', 'date_checked')
    list_filter = ('cleared',)
    search_fields = ('transcript_request__student__name', 'officer_name')

@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ('transcript_id', 'transcript_request', 'generated_by', 'date_generated', 'dean_signature', 'registrar_signature')
    list_filter = ('dean_signature', 'registrar_signature')
    search_fields = ('transcript_request__student__name', 'transcript_id')

@admin.register(TranscriptApproval)
class TranscriptApprovalAdmin(admin.ModelAdmin):
    list_display = ('transcript', 'approved', 'approved_by', 'date_approved')
    list_filter = ('approved',)
    search_fields = ('transcript__transcript_request__student__name', 'approved_by')

@admin.register(TranscriptVerification)
class TranscriptVerificationAdmin(admin.ModelAdmin):
    list_display = ('transcript', 'barcode', 'verified', 'date_verified')
    list_filter = ('verified',)
    search_fields = ('transcript__transcript_request__student__name', 'barcode')


from .models import StaffProfile

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_id', 'role')
    search_fields = ('user__username', 'staff_id', 'role')
    
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    list_filter = ('department',)
    search_fields = ('name', 'department__department')