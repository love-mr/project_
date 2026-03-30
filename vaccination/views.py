
from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.u

from httpx import requesttils import timezone
from datetime import date, timedelta
import random

from .models import User, Child, Vaccine, Hospital, Appointment, VaccinationRecord, Certificate
from .forms import (
    ParentRegistrationForm, StaffRegistrationForm,
    ChildForm, AppointmentForm, QuickAppointmentForm,
)
from .utils import (
    get_due_vaccines, get_upcoming_reminders, get_missed_vaccines, predict_vaccine,
)


# ─── Decorators ──────────────────────────────────────────────────────
def parent_required(view_func):
    """Only allow verified Parent users."""
    def check_parent(u):
        if not u.is_parent:
            return False
        if not u.email_verified:
            return False
        return True

    decorated = login_required(
        user_passes_test(check_parent, login_url='verify_email')(view_func)
    )
    return decorated


def staff_required(view_func):
    """Only allow verified Staff users."""
    def check_staff(u):
        if not u.is_staff_member:
            return False
        if not u.email_verified:
            return False
        return True

    decorated = login_required(
        user_passes_test(check_staff, login_url='verify_email')(view_func)
    )
    return decorated


import threading

def send_verification_email(user):
    code = f"{random.randint(100000,999999)}"
    user.email_verification_code = code
    user.email_verification_code_created_at = timezone.now()
    user.email_verified = False
    user.save()

    email_subject = 'Verify your email for Child Vaccination'
    email_body = (
        f"Hello {user.username},\n\n"
        f"Your verification code is: {code}\n"
        "This code is valid for 15 minutes.\n\n"
        "Thank you!"
    )

    def send():
        try:
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True
            )
        except Exception as e:
            print(f"[Email error] {e}")

    # 🔥 BACKGROUND THREAD (THIS FIXES YOUR ERROR)
    threading.Thread(target=send).start()

    return True


# ─── Authentication ──────────────────────────────────────────────────
def home(request):
    """Landing page."""
    total_hospitals = Hospital.objects.filter(is_active=True).count()

    # Show stats only for logged-in parents (their own children/records).
    # Guests and non-parent users will see zeros (so the counters reflect "their" data).
    if request.user.is_authenticated and request.user.is_parent:
        total_children = Child.objects.filter(parent=request.user).count()
        total_vaccinations = VaccinationRecord.objects.filter(child__parent=request.user).count()
    else:
        total_children = 0
        total_vaccinations = 0

    context = {
        'total_children': total_children,
        'total_vaccinations': total_vaccinations,
        'total_hospitals': total_hospitals,
    }
    return render(request, 'vaccination/home.html', context)


def register(request):
    """Register new parent or staff account."""
    user_type = request.GET.get('type', 'parent')
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'parent')
        if user_type == 'staff':
            form = StaffRegistrationForm(request.POST)
        else:
            form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user)   # 🔥 don't wait for result
            login(request, user)
            messages.success(request, '✅ Account created successfully! Check your email for verification code.')
            return redirect('verify_email')
            
        else:
            messages.error(request, '❌ Please correct the errors below.')
    else:
        if user_type == 'staff':
            form = StaffRegistrationForm()
        else:
            form = ParentRegistrationForm()
    return render(request, 'vaccination/register.html', {
        'form': form,
        'user_type': user_type,
    })


def login_view(request):
    """Login with role selection and simple captcha."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user_type = request.POST.get('user_type', 'parent')
        captcha_val = request.session.get('captcha_val')
        captcha_answer = request.POST.get('captcha_answer', '')

        # Validate captcha
        if str(captcha_val) != captcha_answer.strip():
            messages.error(request, '❌ Captcha answer is incorrect.')
            return redirect('login')

        # Admin authentication (superuser)
        if user_type == 'admin':
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_superuser:
                login(request, user)
                return redirect('admin:index')
            messages.error(request, '❌ Invalid admin credentials.')
            return redirect('login')

        # Normal auth
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user_type == 'parent' and user.is_parent:
                if not user.email_verified:
                    login(request, user)
                    messages.warning(request, '✅ Please verify your email before using the system.')
                    return redirect('verify_email')
                login(request, user)
                return redirect('parent_dashboard')
            elif user_type == 'staff' and user.is_staff_member:
                if not user.email_verified:
                    login(request, user)
                    messages.warning(request, '✅ Please verify your email before using the system.')
                    return redirect('verify_email')
                login(request, user)
                return redirect('staff_dashboard')
            else:
                messages.error(request, '❌ Your account type does not match the selected role.')
        else:
            messages.error(request, '❌ Invalid username or password.')
        return redirect('login')

    # Generate captcha
    a, b = random.randint(1, 9), random.randint(1, 9)
    request.session['captcha_val'] = a + b
    
    # Stats for login page
    total_children = Child.objects.count()
    total_vaccinations = VaccinationRecord.objects.count()
    total_hospitals = Hospital.objects.filter(is_active=True).count()
    
    return render(request, 'vaccination/login.html', {
        'captcha_q': f"{a} + {b} = ?",
        'total_children': total_children,
        'total_vaccinations': total_vaccinations,
        'total_hospitals': total_hospitals,
    })


def resend_verification_code(request):
    """Resend verification code to user email."""
    if not request.user.is_authenticated:
        messages.error(request, '❌ Please log in to resend verification code.')
        return redirect('login')

    if request.user.email_verified:
        messages.info(request, '✅ Your email is already verified.')
        return redirect('parent_dashboard' if request.user.is_parent else 'staff_dashboard')

    if send_verification_email(request.user):
        messages.error(request, '❌ Could not send verification code. Check SMTP settings.')
        return redirect('verify_email')

    messages.success(request, '✅ New verification code sent to your email.')
    return redirect('verify_email')


def verify_email(request):
    """Verify email address after account registration."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if not request.user.is_authenticated:
            messages.error(request, '❌ Please log in before verifying email.')
            return redirect('login')

        if request.user.email_verified:
            messages.info(request, '✅ Email already verified.')
            return redirect('parent_dashboard' if request.user.is_parent else 'staff_dashboard')

        code_expiry = request.user.email_verification_code_created_at + timedelta(minutes=15) if request.user.email_verification_code_created_at else None
        if not request.user.email_verification_code_created_at or timezone.now() > code_expiry:
            messages.error(request, '❌ Verification code expired. Please resend code and try again.')
            return redirect('verify_email')

        if request.user.email_verification_code == code:
            request.user.email_verified = True
            request.user.email_verification_code = ''
            request.user.email_verification_code_created_at = None
            request.user.save()
            messages.success(request, '✅ Email verified successfully. You can now access your dashboard.')
            if request.user.is_parent:
                return redirect('parent_dashboard')
            return redirect('staff_dashboard')

        messages.error(request, '❌ Invalid verification code. Please try again.')
        return redirect('verify_email')

    return render(request, 'vaccination/verify_email.html')


def logout_view(request):
    logout(request)
    messages.success(request, '👋 Logged out successfully.')
    return redirect('home')


# ─── Parent Views ────────────────────────────────────────────────────
@parent_required
def parent_dashboard(request):
    """Parent's main dashboard with stats, children, appointments, reminders."""
    children = Child.objects.filter(parent=request.user)
    appointments = Appointment.objects.filter(child__parent=request.user).select_related(
        'child', 'vaccine', 'hospital'
    )
    reminders = get_upcoming_reminders(request.user)

    # Stats
    total_children = children.count()
    completed_count = appointments.filter(status='completed').count()
    pending_count = appointments.filter(status='pending').count()
    approved_count = appointments.filter(status='approved').count()

    context = {
        'children': children,
        'appointments': appointments[:10],
        'reminders': reminders,
        'total_children': total_children,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
    }
    return render(request, 'vaccination/parent_dashboard.html', context)


@parent_required
def add_child(request):
    """Add a new child."""
    if request.method == 'POST':
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user
            child.save()
            messages.success(request, f'✅ {child.name} has been added successfully!')
            return redirect('child_detail', child_id=child.id)
    else:
        form = ChildForm()
    return render(request, 'vaccination/add_child.html', {'form': form, 'edit': False})


@parent_required
def edit_child(request, child_id):
    """Edit an existing child."""
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        form = ChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ {child.name}\'s details updated!')
            return redirect('child_detail', child_id=child.id)
    else:
        form = ChildForm(instance=child)
    return render(request, 'vaccination/add_child.html', {'form': form, 'edit': True, 'child': child})


@parent_required
def delete_child(request, child_id):
    """Delete a child (POST only)."""
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        name = child.name
        child.delete()
        messages.success(request, f'🗑️ {name} removed from your records.')
    return redirect('parent_dashboard')


@parent_required
def child_detail(request, child_id):
    """View child details, vaccination history, due vaccines."""
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    due_vaccines = get_due_vaccines(child)
    missed_vaccines = get_missed_vaccines(child)
    records = VaccinationRecord.objects.filter(child=child).select_related('vaccine')
    appointments = Appointment.objects.filter(child=child).select_related('vaccine', 'hospital')

    context = {
        'child': child,
        'due_vaccines': due_vaccines,
        'missed_vaccines': missed_vaccines,
        'records': records,
        'appointments': appointments,
    }
    return render(request, 'vaccination/child_detail.html', context)


@parent_required
def book_appointment(request):
    """Book a vaccination appointment."""
    if request.method == 'POST':
        form = AppointmentForm(request.POST, parent=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.save()
            # Send email notification
            try:
                send_mail(
                    'Vaccination Appointment Booked',
                    f'Dear {request.user.username},\n\n'
                    f'Your appointment for {appointment.child.name} '
                    f'({appointment.vaccine.name}) at {appointment.hospital.name} '
                    f'on {appointment.preferred_date} has been booked.\n'
                    f'Status: Pending approval.\n\nThank you!',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, f'✅ Appointment booked! Awaiting staff approval.')
            return redirect('parent_dashboard')
    else:
        child_id = request.GET.get('child')
        vaccine_id = request.GET.get('vaccine')
        initial = {}
        if child_id:
            initial['child'] = child_id
        if vaccine_id:
            initial['vaccine'] = vaccine_id
        form = AppointmentForm(parent=request.user, initial=initial)

    return render(request, 'vaccination/book_appointment.html', {'form': form})


@parent_required
def vaccination_records(request):
    """View all vaccination records for parent's children."""
    records = VaccinationRecord.objects.filter(
        child__parent=request.user
    ).select_related('child', 'vaccine', 'appointment__hospital')
    return render(request, 'vaccination/vaccination_records.html', {'records': records})


@parent_required
def certificate_view(request, record_id):
    """View/download vaccination certificate."""
    record = get_object_or_404(VaccinationRecord, id=record_id, child__parent=request.user)
    cert = getattr(record, 'certificate', None)
    if not cert:
        messages.error(request, 'Certificate not yet generated.')
        return redirect('vaccination_records')
    return render(request, 'vaccination/certificate.html', {'certificate': cert, 'record': record})


# ─── Staff Views ─────────────────────────────────────────────────────
@staff_required
def staff_dashboard(request):
    """Staff main dashboard with stats and pending appointments."""
    pending = Appointment.objects.filter(status='pending').select_related(
        'child', 'child__parent', 'vaccine', 'hospital'
    )
    approved = Appointment.objects.filter(status='approved').select_related(
        'child', 'child__parent', 'vaccine', 'hospital'
    )
    recent_records = VaccinationRecord.objects.all().select_related(
        'child', 'vaccine'
    )[:10]

    # Stats
    total_pending = pending.count()
    total_approved = approved.count()
    total_completed = VaccinationRecord.objects.count()
    total_children = Child.objects.count()
    total_vaccines = Vaccine.objects.count()

    # Vaccine stock info
    vaccine_stock = Vaccine.objects.all()

    context = {
        'pending': pending,
        'approved': approved,
        'recent_records': recent_records,
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_completed': total_completed,
        'total_children': total_children,
        'total_vaccines': total_vaccines,
        'vaccine_stock': vaccine_stock,
    }
    return render(request, 'vaccination/staff_dashboard.html', context)


@staff_required
def approve_appointment(request, appt_id):
    """Approve a pending appointment."""
    appt = Appointment.objects.filter(id=appt_id, status='pending').first()
    if not appt:
        messages.error(request, '❌ Appointment not found or already processed.')
        return redirect('staff_dashboard')

    appt.status = 'approved'
    appt.save()

    # Notify parent
    try:
        send_mail(
            'Appointment Approved ✅',
            f'Dear {appt.child.parent.username},\n\n'
            f'Your vaccination appointment for {appt.child.name} '
            f'({appt.vaccine.name}) at {appt.hospital.name} '
            f'on {appt.preferred_date} has been APPROVED.\n\n'
            f'Please arrive on time.\n\nThank you!',
            settings.DEFAULT_FROM_EMAIL,
            [appt.child.parent.email],
            fail_silently=True,
        )
    except Exception:
        pass
    messages.success(request, f'✅ Appointment for {appt.child.name} approved! Parent notified.')
    return redirect('staff_dashboard')


@staff_required
def reject_appointment(request, appt_id):
    """Reject a pending appointment."""
    appt = get_object_or_404(Appointment, id=appt_id, status='pending')
    appt.status = 'rejected'
    appt.save()
    messages.warning(request, f'❌ Appointment for {appt.child.name} rejected.')
    return redirect('staff_dashboard')


@staff_required
def complete_vaccination(request, appt_id):
    """Mark appointment as completed and create vaccination record + certificate."""
    appt = get_object_or_404(Appointment, id=appt_id, status='approved')
    notes = request.POST.get('notes', '') if request.method == 'POST' else ''

    # Create vaccination record
    record = VaccinationRecord.objects.create(
        appointment=appt,
        child=appt.child,
        vaccine=appt.vaccine,
        date_administered=date.today(),
        administered_by=request.user,
        notes=notes,
    )

    # Generate certificate
    cert = Certificate.objects.create(record=record)

    # Update appointment status
    appt.status = 'completed'
    appt.save()

    # Decrease vaccine stock
    vaccine = appt.vaccine
    if vaccine.stock > 0:
        vaccine.stock -= 1
        vaccine.save()

    # Send certificate email to parent
    try:
        send_mail(
            'Vaccination Completed: Certificate Issued',
            f'Hello {appt.child.parent.username},\n\n'
            f'Vaccination for {appt.child.name} ({appt.vaccine.name}) has been completed.\n'
            f'Certificate ID: {cert.certificate_id}\n'
            f'Date: {cert.issued_at.strftime("%Y-%m-%d %H:%M") if cert.issued_at else "N/A"}\n\n'
            'You can login and view/download your certificate from your dashboard.\n\n'
            'Thank you!\n',
            settings.DEFAULT_FROM_EMAIL,
            [appt.child.parent.email],
            fail_silently=True,
        )
    except Exception:
        messages.warning(request, '⚠️ Certificate email could not be sent; please check SMTP settings.')

    messages.success(
        request,
        f'✅ Vaccination completed for {appt.child.name}! Certificate generated and emailed to parent.'
    )
    return redirect('staff_dashboard')


@staff_required
def all_children(request):
    """View all children in the system."""
    children = Child.objects.all().select_related('parent')
    return render(request, 'vaccination/all_children.html', {'children': children})


@staff_required
def all_records(request):
    """View all vaccination records."""
    records = VaccinationRecord.objects.all().select_related(
        'child', 'vaccine', 'administered_by', 'appointment__hospital'
    )
    return render(request, 'vaccination/all_records.html', {'records': records})


@staff_required
def staff_certificate_view(request, record_id):
    """Staff view of a vaccination certificate."""
    record = get_object_or_404(VaccinationRecord, id=record_id)
    cert = getattr(record, 'certificate', None)
    if not cert:
        messages.error(request, 'Certificate not yet generated.')
        return redirect('staff_dashboard')
    return render(request, 'vaccination/certificate.html', {'certificate': cert, 'record': record})
