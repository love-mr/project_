"""
Django management command to seed the database with vaccine schedule and hospitals.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from vaccination.models import Vaccine, Hospital


class Command(BaseCommand):
    help = 'Seed the database with standard vaccines and sample hospitals'

    def handle(self, *args, **kwargs):
        self.seed_vaccines()
        self.seed_hospitals()
        self.stdout.write(self.style.SUCCESS('[OK] Database seeded successfully!'))

    def seed_vaccines(self):
        vaccines = [
            ('BCG', 0, 1, 'Bacillus Calmette-Guerin — Tuberculosis protection'),
            ('Hepatitis B', 0, 1, 'Hepatitis B — Birth dose'),
            ('OPV', 0, 0, 'Oral Polio Vaccine — Zero dose at birth'),
            ('Hepatitis B', 1, 2, 'Hepatitis B — 2nd dose'),
            ('OPV', 2, 1, 'Oral Polio Vaccine — 1st dose'),
            ('Pentavalent (DPT+HepB+Hib)', 2, 1, 'DPT + HepB + Hib combination — 1st dose'),
            ('Rotavirus', 2, 1, 'Rotavirus vaccine — 1st dose'),
            ('PCV', 2, 1, 'Pneumococcal Conjugate Vaccine — 1st dose'),
            ('OPV', 4, 2, 'Oral Polio Vaccine — 2nd dose'),
            ('Pentavalent (DPT+HepB+Hib)', 4, 2, 'DPT + HepB + Hib combination — 2nd dose'),
            ('Rotavirus', 4, 2, 'Rotavirus vaccine — 2nd dose'),
            ('OPV', 6, 3, 'Oral Polio Vaccine — 3rd dose'),
            ('Pentavalent (DPT+HepB+Hib)', 6, 3, 'DPT + HepB + Hib combination — 3rd dose'),
            ('Rotavirus', 6, 3, 'Rotavirus vaccine — 3rd dose'),
            ('IPV', 6, 1, 'Injectable Polio Vaccine — 1st dose'),
            ('Measles / MR', 9, 1, 'Measles or Measles-Rubella — 1st dose'),
            ('PCV Booster', 9, 2, 'Pneumococcal Conjugate Vaccine — Booster'),
            ('Hepatitis A', 12, 1, 'Hepatitis A — 1st dose'),
            ('MMR', 12, 1, 'Measles Mumps Rubella — 1st dose'),
            ('Varicella', 15, 1, 'Chickenpox — 1st dose'),
            ('DPT Booster', 18, 1, 'DPT — 1st Booster'),
            ('OPV Booster', 18, 4, 'Oral Polio Vaccine — Booster dose'),
            ('Hepatitis A', 18, 2, 'Hepatitis A — 2nd dose'),
            ('MMR', 48, 2, 'Measles Mumps Rubella — 2nd dose'),
            ('DPT Booster', 60, 2, 'DPT — 2nd Booster'),
            ('Varicella', 60, 2, 'Chickenpox — 2nd dose'),
        ]

        created = 0
        for name, age, dose, desc in vaccines:
            _, was_created = Vaccine.objects.get_or_create(
                name=name,
                recommended_age_months=age,
                dose_number=dose,
                defaults={'description': desc, 'stock': 100},
            )
            if was_created:
                created += 1
        self.stdout.write(f'  [VACCINES] {created} created, {len(vaccines) - created} already existed')

    def seed_hospitals(self):
        hospitals = [
            ('City General Hospital', '123 Main Street, City Center', '044-2345678'),
            ('Rainbow Children\'s Hospital', '45 Anna Nagar, Chennai', '044-8765432'),
            ('Apollo Children\'s Hospital', '21 Greams Lane, Chennai', '044-2829100'),
            ('Government Children\'s Hospital', '12 Egmore, Chennai', '044-2819200'),
            ('SRMC Hospital', '100 Porur, Chennai', '044-2467890'),
        ]

        created = 0
        for name, address, phone in hospitals:
            _, was_created = Hospital.objects.get_or_create(
                name=name,
                defaults={'address': address, 'phone': phone},
            )
            if was_created:
                created += 1
        self.stdout.write(f'  [HOSPITALS] {created} created, {len(hospitals) - created} already existed')
