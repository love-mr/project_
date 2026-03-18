from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Child, Vaccine, Hospital, Appointment, VaccinationRecord
from datetime import date
from dateutil.relativedelta import relativedelta


class ModelTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username='parent1', password='testpass123', is_parent=True, email='p@test.com'
        )
        self.staff = User.objects.create_user(
            username='staff1', password='testpass123', is_staff_member=True, email='s@test.com'
        )
        self.child = Child.objects.create(
            name='TestChild', dob=date.today() - relativedelta(months=6),
            gender='M', weight=7.5, blood_group='O+', parent=self.parent
        )
        self.vaccine = Vaccine.objects.create(
            name='TestVax', recommended_age_months=6, dose_number=1, stock=50
        )
        self.hospital = Hospital.objects.create(
            name='TestHospital', address='123 Test St', phone='1234567890'
        )

    def test_child_age(self):
        self.assertGreaterEqual(self.child.age_months, 5)
        self.assertIn('mo', self.child.age_display)

    def test_appointment_creation(self):
        appt = Appointment.objects.create(
            child=self.child, vaccine=self.vaccine,
            hospital=self.hospital, preferred_date=date.today()
        )
        self.assertEqual(appt.status, 'pending')
        self.assertEqual(str(appt), f'TestChild — TestVax (pending)')

    def test_vaccination_record(self):
        appt = Appointment.objects.create(
            child=self.child, vaccine=self.vaccine,
            hospital=self.hospital, preferred_date=date.today(),
            status='approved'
        )
        record = VaccinationRecord.objects.create(
            appointment=appt, child=self.child, vaccine=self.vaccine,
            administered_by=self.staff
        )
        self.assertEqual(record.date_administered, date.today())


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.parent = User.objects.create_user(
            username='testparent', password='testpass123', is_parent=True, email='p@t.com'
        )
        self.staff = User.objects.create_user(
            username='teststaff', password='testpass123', is_staff_member=True, email='s@t.com'
        )

    def test_home_page(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

    def test_login_page(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'captcha')

    def test_register_page(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)

    def test_parent_dashboard_requires_login(self):
        resp = self.client.get(reverse('parent_dashboard'))
        self.assertNotEqual(resp.status_code, 200)

    def test_staff_dashboard_requires_login(self):
        resp = self.client.get(reverse('staff_dashboard'))
        self.assertNotEqual(resp.status_code, 200)

    def test_parent_can_access_dashboard(self):
        self.client.login(username='testparent', password='testpass123')
        resp = self.client.get(reverse('parent_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_staff_can_access_dashboard(self):
        self.client.login(username='teststaff', password='testpass123')
        resp = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(resp.status_code, 200)
