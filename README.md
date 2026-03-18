# Child Vaccination Django App

This project implements a responsive web frontend and Django backend for a child vaccination system. It includes three roles – Parent, Staff, and Admin – following the specifications.

## Setup Instructions

1. **Create and activate a virtual environment** (already set up at project root):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install dependencies**
   ```powershell
   pip install django djongo
   ```
   If you are using a real MongoDB instance, configure `DATABASES` in `childvaccination_project/settings.py` accordingly.

3. **Make migrations and migrate**
   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser**
   ```powershell
   python manage.py createsuperuser --username Devil --email admin@example.com
   # use password Devil for consistent admin login
   ```

   This account will allow direct access to the Django admin interface under `/admin/`.

5. **Run development server**
   ```powershell
   python manage.py runserver
   ```

6. **Access the application**
   - Visit http://127.0.0.1:8000/ for the frontend.
   - Admin interface at http://127.0.0.1:8000/admin/ (login as Devil/Devil).

## Features

- **User Authentication**: login page with user type and captcha; registration for parent or staff.
- **Parent role**: book appointments with age-based vaccine assignment.
- **Staff role**: view pending appointments and accept, sending console emails.
- **Admin role**: manage users, change passwords, view vaccine stock, and generate certificates.

## Code Overview

- `vaccination/models.py`: custom user, child, appointment, vaccine, certificate models.
- `vaccination/views.py`: handlers for authentication and dashboards.
- `vaccination/templates/`: HTML templates with responsive CSS/JS.
- `static/`: CSS and JS resources.

> Note: an actual ML model is simulated by the `assign_vaccine` function in views; you can replace this with a real model in `vaccination/ml_model.py`.

## Extending the Application

- Add real machine learning by implementing `vaccination/ml_model.py` and importing it in `assign_vaccine`.
- Improve captcha with a library such as `django-simple-captcha`.
- Send real emails by configuring the SMTP backend in `settings.py`.
- Add certificate generation logic when appointments are marked completed.

---

This README provides a starting point to get the application running and to further develop features as required.