"""Assessment forms."""
from django import forms
from .models import HealthAssessment

YES_NO_CHOICES = [('', 'Select...'), ('no', 'No'), ('yes', 'Yes'), ('sometimes', 'Sometimes'), ('unsure', 'Not Sure')]
PAIN_SCALE = [(i, str(i)) for i in range(0, 11)]


class HealthAssessmentForm(forms.ModelForm):
    class Meta:
        model = HealthAssessment
        exclude = ['user', 'risk_level', 'submitted_at']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120, 'placeholder': 'Your age'}),
            'chest_discomfort': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'chest_pain_level': forms.Select(attrs={'class': 'form-select'}, choices=[(i, str(i)) for i in range(11)]),
            'shortness_of_breath': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'shortness_at_rest': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'dizziness': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'fainting': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'fatigue': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'palpitations': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'swollen_ankles': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'smoker': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'diabetes': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'high_blood_pressure': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'family_heart_history': forms.Select(attrs={'class': 'form-select'}, choices=YES_NO_CHOICES),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Any other symptoms or concerns you would like to mention...'
            }),
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and (age < 1 or age > 120):
            raise forms.ValidationError('Please enter a valid age between 1 and 120.')
        return age
