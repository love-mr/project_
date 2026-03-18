from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Child, Appointment, Hospital, Vaccine


class ParentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-input',
                'autocomplete': 'off',
            })
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['email'].widget.attrs['placeholder'] = 'your@email.com'
        self.fields['phone'].widget.attrs['placeholder'] = 'Phone number'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_parent = True
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class StaffRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-input',
                'autocomplete': 'off',
            })
        self.fields['username'].widget.attrs['placeholder'] = 'Choose a username'
        self.fields['email'].widget.attrs['placeholder'] = 'your@email.com'
        self.fields['phone'].widget.attrs['placeholder'] = 'Phone number'
        self.fields['password1'].widget.attrs['placeholder'] = 'Create password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff_member = True
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'dob', 'gender', 'weight', 'blood_group']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Child\'s full name'}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'weight': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Weight in kg', 'step': '0.01'}),
            'blood_group': forms.Select(attrs={'class': 'form-input'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['child', 'vaccine', 'hospital', 'preferred_date', 'notes']
        widgets = {
            'child': forms.Select(attrs={'class': 'form-input'}),
            'vaccine': forms.Select(attrs={'class': 'form-input'}),
            'hospital': forms.Select(attrs={'class': 'form-input'}),
            'preferred_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Any special notes...'}),
        }

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent:
            self.fields['child'].queryset = Child.objects.filter(parent=parent)
        self.fields['hospital'].queryset = Hospital.objects.filter(is_active=True)


class QuickAppointmentForm(forms.Form):
    """Simplified form for quick booking from parent dashboard."""
    child_name = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'class': 'form-input', 'placeholder': 'Child\'s name'}
    ))
    child_age = forms.IntegerField(min_value=0, max_value=60, widget=forms.NumberInput(
        attrs={'class': 'form-input', 'placeholder': 'Age in months'}
    ))
    parent_email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-input', 'placeholder': 'Your email'}
    ))
