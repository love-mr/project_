from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Child, Vaccine, Hospital, Appointment, VaccinationRecord, Certificate


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Role', {'fields': ('is_parent', 'is_staff_member', 'phone')}),
    )
    list_display = ('username', 'email', 'is_parent', 'is_staff_member', 'is_superuser')
    list_filter = ('is_parent', 'is_staff_member', 'is_superuser')
    search_fields = ('username', 'email')


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'dob', 'gender', 'weight', 'blood_group', 'parent', 'age_display')
    list_filter = ('gender', 'blood_group')
    search_fields = ('name', 'parent__username')

    def age_display(self, obj):
        return obj.age_display
    age_display.short_description = 'Age'


@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    list_display = ('name', 'dose_number', 'recommended_age_months', 'stock')
    list_filter = ('dose_number',)
    search_fields = ('name',)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('child', 'vaccine', 'hospital', 'preferred_date', 'status', 'created_at')
    list_filter = ('status', 'hospital')
    search_fields = ('child__name', 'vaccine__name')
    date_hierarchy = 'preferred_date'


@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ('child', 'vaccine', 'date_administered', 'administered_by')
    list_filter = ('date_administered',)
    search_fields = ('child__name', 'vaccine__name')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'record', 'issued_at')
    search_fields = ('certificate_id',)
