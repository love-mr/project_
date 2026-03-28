from django.urls import path
from . import views

urlpatterns = [
    # ─── Public ────────────────────────────────────────────
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verify-email/resend/', views.resend_verification_code, name='resend_verification_code'),

    # ─── Parent ────────────────────────────────────────────
    path('parent/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/add-child/', views.add_child, name='add_child'),
    path('parent/edit-child/<int:child_id>/', views.edit_child, name='edit_child'),
    path('parent/delete-child/<int:child_id>/', views.delete_child, name='delete_child'),
    path('parent/child/<int:child_id>/', views.child_detail, name='child_detail'),
    path('parent/book-appointment/', views.book_appointment, name='book_appointment'),
    path('parent/records/', views.vaccination_records, name='vaccination_records'),
    path('parent/certificate/<int:record_id>/', views.certificate_view, name='certificate_view'),

    # ─── Staff ─────────────────────────────────────────────
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/approve/<int:appt_id>/', views.approve_appointment, name='approve_appointment'),
    path('staff/reject/<int:appt_id>/', views.reject_appointment, name='reject_appointment'),
    path('staff/complete/<int:appt_id>/', views.complete_vaccination, name='complete_vaccination'),
    path('staff/children/', views.all_children, name='all_children'),
    path('staff/records/', views.all_records, name='all_records'),
    path('staff/certificate/<int:record_id>/', views.staff_certificate_view, name='staff_certificate_view'),
]