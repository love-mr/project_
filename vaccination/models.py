from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta


class User(AbstractUser):
    """Custom user supporting Parent, Staff, and Admin roles."""
    is_parent = models.BooleanField(default=False)
    is_staff_member = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)

    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    email_verification_code_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        role = 'Parent' if self.is_parent else ('Staff' if self.is_staff_member else 'Admin')
        verified = '✓' if self.email_verified else '✗'
        return f"{self.username} ({role}, email_verified={verified})"


class Child(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    name = models.CharField(max_length=100)
    dob = models.DateField(verbose_name='Date of Birth')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text='Weight in kg')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def age_months(self):
        """Calculate age in months from DOB."""
        today = date.today()
        delta = relativedelta(today, self.dob)
        return delta.years * 12 + delta.months

    @property
    def age_display(self):
        """Human-readable age string."""
        today = date.today()
        delta = relativedelta(today, self.dob)
        if delta.years > 0:
            return f"{delta.years} yr{'s' if delta.years > 1 else ''} {delta.months} mo"
        return f"{delta.months} month{'s' if delta.months != 1 else ''}"

    def __str__(self):
        return f"{self.name} ({self.age_display})"


class Vaccine(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    recommended_age_months = models.PositiveIntegerField(
        help_text='Recommended age in months for this vaccine'
    )
    dose_number = models.PositiveIntegerField(default=1)
    stock = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['recommended_age_months', 'dose_number']

    def __str__(self):
        return f"{self.name} (Dose {self.dose_number}) — Age {self.recommended_age_months} mo"


class Hospital(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='appointments')
    vaccine = models.ForeignKey(Vaccine, on_delete=models.CASCADE, related_name='appointments')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='appointments')
    preferred_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.child.name} — {self.vaccine.name} ({self.status})"


class VaccinationRecord(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name='record'
    )
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='vaccination_records')
    vaccine = models.ForeignKey(Vaccine, on_delete=models.CASCADE, related_name='records')
    date_administered = models.DateField(default=date.today)
    administered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='administered_records'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_administered']

    def __str__(self):
        return f"{self.child.name} — {self.vaccine.name} on {self.date_administered}"


class Certificate(models.Model):
    record = models.OneToOneField(
        VaccinationRecord, on_delete=models.CASCADE, related_name='certificate'
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=20, unique=True)

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            import uuid
            self.certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificate {self.certificate_id} for {self.record.child.name}"