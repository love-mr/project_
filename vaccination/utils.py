"""
Utility functions for vaccine scheduling, reminders, and age-based recommendations.
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from .models import Vaccine, Appointment, VaccinationRecord


# Standard childhood vaccine schedule (age in months)
VACCINE_SCHEDULE = [
    {'name': 'BCG', 'age_months': 0, 'dose': 1, 'desc': 'Bacillus Calmette-Guerin — Tuberculosis'},
    {'name': 'Hepatitis B', 'age_months': 0, 'dose': 1, 'desc': 'Hepatitis B — Birth dose'},
    {'name': 'OPV', 'age_months': 0, 'dose': 0, 'desc': 'Oral Polio Vaccine — Zero dose'},
    {'name': 'Hepatitis B', 'age_months': 1, 'dose': 2, 'desc': 'Hepatitis B — 2nd dose'},
    {'name': 'OPV', 'age_months': 2, 'dose': 1, 'desc': 'Oral Polio Vaccine — 1st dose'},
    {'name': 'Pentavalent', 'age_months': 2, 'dose': 1, 'desc': 'DPT + HepB + Hib — 1st dose'},
    {'name': 'Rotavirus', 'age_months': 2, 'dose': 1, 'desc': 'Rotavirus — 1st dose'},
    {'name': 'PCV', 'age_months': 2, 'dose': 1, 'desc': 'Pneumococcal Conjugate Vaccine — 1st dose'},
    {'name': 'OPV', 'age_months': 4, 'dose': 2, 'desc': 'Oral Polio Vaccine — 2nd dose'},
    {'name': 'Pentavalent', 'age_months': 4, 'dose': 2, 'desc': 'DPT + HepB + Hib — 2nd dose'},
    {'name': 'Rotavirus', 'age_months': 4, 'dose': 2, 'desc': 'Rotavirus — 2nd dose'},
    {'name': 'OPV', 'age_months': 6, 'dose': 3, 'desc': 'Oral Polio Vaccine — 3rd dose'},
    {'name': 'Pentavalent', 'age_months': 6, 'dose': 3, 'desc': 'DPT + HepB + Hib — 3rd dose'},
    {'name': 'Rotavirus', 'age_months': 6, 'dose': 3, 'desc': 'Rotavirus — 3rd dose'},
    {'name': 'IPV', 'age_months': 6, 'dose': 1, 'desc': 'Injectable Polio Vaccine — 1st dose'},
    {'name': 'Measles/MR', 'age_months': 9, 'dose': 1, 'desc': 'Measles / Measles-Rubella — 1st dose'},
    {'name': 'PCV', 'age_months': 9, 'dose': 2, 'desc': 'Pneumococcal Conjugate Vaccine — Booster'},
    {'name': 'Hepatitis A', 'age_months': 12, 'dose': 1, 'desc': 'Hepatitis A — 1st dose'},
    {'name': 'MMR', 'age_months': 12, 'dose': 1, 'desc': 'Measles Mumps Rubella — 1st dose'},
    {'name': 'Varicella', 'age_months': 15, 'dose': 1, 'desc': 'Chickenpox — 1st dose'},
    {'name': 'DPT Booster', 'age_months': 18, 'dose': 1, 'desc': 'DPT — 1st Booster'},
    {'name': 'OPV Booster', 'age_months': 18, 'dose': 4, 'desc': 'Oral Polio — Booster'},
    {'name': 'Hepatitis A', 'age_months': 18, 'dose': 2, 'desc': 'Hepatitis A — 2nd dose'},
    {'name': 'MMR', 'age_months': 48, 'dose': 2, 'desc': 'Measles Mumps Rubella — 2nd dose'},
    {'name': 'DPT Booster', 'age_months': 60, 'dose': 2, 'desc': 'DPT — 2nd Booster'},
    {'name': 'Varicella', 'age_months': 60, 'dose': 2, 'desc': 'Chickenpox — 2nd dose'},
]


def predict_vaccine(age_months):
    """
    ML-style vaccine prediction based on child age.
    Returns the best-matching vaccine name for the given age in months.
    """
    best_match = None
    min_diff = float('inf')
    for entry in VACCINE_SCHEDULE:
        diff = abs(entry['age_months'] - age_months)
        if diff < min_diff:
            min_diff = diff
            best_match = entry['name']
    return best_match or 'General Checkup'


def get_due_vaccines(child):
    """
    Returns list of vaccines that are due for a child based on age.
    Excludes vaccines already administered.
    """
    age_months = child.age_months

    # Get administered vaccine IDs
    administered = set(
        VaccinationRecord.objects.filter(child=child)
        .values_list('vaccine_id', flat=True)
    )

    # Also exclude vaccines with pending/approved appointments
    in_progress = set(
        Appointment.objects.filter(
            child=child,
            status__in=['pending', 'approved']
        ).values_list('vaccine_id', flat=True)
    )

    due = []
    all_vaccines = Vaccine.objects.all()
    for vaccine in all_vaccines:
        if vaccine.id in administered or vaccine.id in in_progress:
            continue
        if vaccine.recommended_age_months <= age_months:
            status = 'overdue'
        elif vaccine.recommended_age_months <= age_months + 2:
            status = 'upcoming'
        else:
            status = 'future'
        due.append({
            'vaccine': vaccine,
            'status': status,
            'recommended_age': vaccine.recommended_age_months,
        })

    # Sort: overdue first, then upcoming, then future
    priority = {'overdue': 0, 'upcoming': 1, 'future': 2}
    due.sort(key=lambda x: (priority[x['status']], x['recommended_age']))
    return due


def get_upcoming_reminders(parent):
    """
    Returns approved appointments in the next 7 days for parent's children.
    """
    today = date.today()
    week_later = today + timedelta(days=7)
    return Appointment.objects.filter(
        child__parent=parent,
        status='approved',
        preferred_date__gte=today,
        preferred_date__lte=week_later,
    ).select_related('child', 'vaccine', 'hospital')


def get_missed_vaccines(child):
    """
    Returns vaccines that are past due (should have been given by now)
    but have no records.
    """
    age_months = child.age_months
    administered_ids = set(
        VaccinationRecord.objects.filter(child=child)
        .values_list('vaccine_id', flat=True)
    )
    in_progress_ids = set(
        Appointment.objects.filter(
            child=child,
            status__in=['pending', 'approved']
        ).values_list('vaccine_id', flat=True)
    )

    missed = []
    for vaccine in Vaccine.objects.filter(recommended_age_months__lt=age_months):
        if vaccine.id not in administered_ids and vaccine.id not in in_progress_ids:
            missed.append(vaccine)
    return missed
