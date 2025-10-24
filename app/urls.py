from django.urls import path
from .import views
from . import batch_views
from django.contrib.auth import views as auth_views
from .forms import ResetPasswordForm, ResetPasswordConfirmForm
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('accounts/login/', views.login_view, name='login'),
    path('student_list', views.student_list, name='student_list'),
    path('student/<int:pk>/', views.student_detail, name='student_detail'),
    path('request/', views.request_transcript, name='request_transcript'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/<int:pk>/payment/', views.update_payment, name='update_payment'),
    path('request/<int:pk>/status/', views.update_status, name='update_status'),
    path('request/<int:pk>/generate/', views.generate_transcript, name='generate_transcript'),
    path('request/<int:pk>/download/', views.student_download_transcript, name='student_download_transcript'),
    path('transcript/<int:pk>/approve/', views.approve_transcript, name='approve_transcript'),
    path('manage-students/', views.manage_students, name='manage_students'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/', views.department_list, name='department_list'), 
    path('departments/update/<int:pk>/', views.update_department, name='update_department'),
    path('departments/delete/<int:pk>/', views.delete_department, name='delete_department'),
    path("signup/", views.signup_view, name="signup"),
    path("upload-students/", views.upload_students, name="upload_students"),
    path('login', views.login_view, name='login'),
    path('create-staff/', views.create_staff, name='create_staff'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('generate-transcript-preview/<int:pk>/', batch_views.generate_transcript_preview, name='generate_transcript_preview'),
    path('transcript-signatures/<int:pk>/', batch_views.update_transcript_signatures, name='update_transcript_signatures'),
    path('verify/<str:code>/', views.verify_transcript, name='verify_transcript'),
    path('qr-scanner/', views.qr_scanner, name='qr_scanner'),
    path('transcript/init-payment/', views.init_transcript_payment, name='init_transcript_payment'),
    path('transcript/payment/verify/', views.verify_transcript_payment, name='verify_transcript_payment'),
    path('transcript/request/', views.request_transcript, name='request_transcript'),
    path('add-registrar/', views.add_faculty_registrar, name='add_faculty_registrar'),
    path('request/<int:pk>/download/', views.download_transcript, name='download_transcript'),
    path('registrar/reapprove/<int:request_id>/', views.registrar_reapprove, name='registrar_reapprove'),
    path("request/<int:pk>/student-download/", views.student_download_transcript, name="student_download_transcript"),
    path('password-reset/', views.password_reset_request, name='app_password_reset_request'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset.html',                                                                 form_class=ResetPasswordForm), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', views.DebugPasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html',
                                                                                     form_class=ResetPasswordConfirmForm), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),
    path('password-reset-confirm/', views.password_reset_confirm, name='app_password_reset_confirm'),
    path('staff/payments/export/excel/', views.export_payments_excel, name='export_payments_excel'),
    path('staff/payments/export/pdf/', views.export_payments_pdf, name='export_payments_pdf'),
    path('notify-payment/<int:pk>/', views.notify_payment_made, name='notify_payment_made'),
    path('approved-transcripts/', views.student_approved_transcripts, name='student_approved_transcripts'),
    path('approved-transcripts/<int:pk>/generate/', views.student_generate_transcript, name='student_generate_transcript'),
    path('momo/callback/', views.momo_callback, name='momo_callback'),
    path('accounts/verification/', views.accounts_verification_queue, name='accounts_verification_queue'),
    path('accounts/verify/<int:pk>/', views.accounts_verify_request, name='accounts_verify_request'),
    path('invoice/<int:pk>/download/', views.download_invoice, name='download_invoice'),
    path('registrar-action/<int:pk>/', views.registrar_action, name='registrar_action'),
    path('change-faculty/<int:pk>/', views.change_faculty_registrar, name='change_faculty_registrar'),
    path('registrar-approve-disapprove/<int:pk>/', views.registrar_approve_disapprove, name='registrar_approve_disapprove'),
    path('exams-office-approve-disapprove/<int:pk>/', views.exams_office_approve_disapprove, name='exams_office_approve_disapprove'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('view_transcript/<str:filename>/', views.serve_transcript_pdf, name='serve_transcript_pdf'),
    path('manual/verify/', views.manual_verify, name='manual_verify'),
    path('superadmin/dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('logins/', views.superadmin_login, name='superadmin_login'),
    path('superadmin/dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/logout/', views.superadmin_logout, name='superadmin_logout'),
path('superadmin/export-payments/', views.export_payments_excel, name='export_payments_excel'),
    path('view_transcript/<str:filename>/', views.serve_transcript_pdf, name='serve_transcript_pdf'),
    path('superadmin/faculty-registrars/', views.manage_faculty_registrars, name='manage_faculty_registrars'),
    path('superadmin/transcript-types/', views.manage_transcript_types, name='manage_transcript_types'),
    path('superadmin/departments/', views.manage_departments, name='manage_departments'),
    path('superadmin/programs/', views.manage_programs, name='manage_programs'),
    path('export-payments/', views.export_staff_payments_excel, name='export_staff_payments_excel'),
    path("registrar/export-payments/", views.registrar_export_payments, name="registrar_export_payments"),
    path('manage-whatsapp-groups/', views.manage_whatsapp_groups, name='manage_whatsapp_groups'),
    path('manage-students/', views.manage_students, name='manage_students'),
    path('', views.landing_page, name='landing_page'),
    path('add-contact/', views.manage_contacts, name='add_contact'),
    path('staff/', views.staff_profile_list, name='staff_profile_list'),
    path('staff/<str:staff_id>/edit/', views.edit_staff_profile, name='edit_staff_profile'),
    path('staff/officer/<str:role>/edit/', views.edit_officer, name='edit_officer'),
    path('staff/officers/', views.officers_list, name='officers_list'),
    path('registrar/upload/<int:pk>/', views.registrar_upload_transcript, name='registrar_upload_transcript'),
    path('registrar/manual-upload/', views.registrar_manual_upload, name='registrar_manual_upload'),
    path('exams-office/manual-upload/', views.exams_office_manual_upload, name='exams_office_manual_upload'),
    path('ajax/student-search/', views.ajax_student_search, name='ajax_student_search'),
















]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)