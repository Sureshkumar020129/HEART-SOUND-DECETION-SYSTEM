"""Health assessment models."""
from django.db import models
from django.contrib.auth.models import User


class HealthAssessment(models.Model):
    """User-submitted heart health symptom questionnaire."""
    PAIN_SCALE = [(i, str(i)) for i in range(0, 11)]
    YES_NO_CHOICES = [('yes', 'Yes'), ('no', 'No'), ('sometimes', 'Sometimes'), ('unsure', 'Not Sure')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    # Demographics
    age = models.PositiveIntegerField(null=True, blank=True, help_text='Age in years')
    # Symptoms
    chest_discomfort = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    chest_pain_level = models.IntegerField(choices=PAIN_SCALE, default=0,
        help_text='0 = no pain, 10 = worst pain')
    shortness_of_breath = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    shortness_at_rest = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    dizziness = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    fainting = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    fatigue = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    palpitations = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    swollen_ankles = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    # Lifestyle
    smoker = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    diabetes = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    high_blood_pressure = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    family_heart_history = models.CharField(max_length=20, choices=YES_NO_CHOICES, default='no')
    # Free text (optional)
    additional_notes = models.TextField(max_length=1000, blank=True)
    # Risk level computed on save
    RISK_CHOICES = [('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High'), ('seek_urgent', 'Seek Urgent Care')]
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='low', editable=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Assessment by {self.user.username} ({self.submitted_at:%Y-%m-%d})"

    def save(self, *args, **kwargs):
        self.risk_level = self._compute_risk()
        super().save(*args, **kwargs)

    def _compute_risk(self) -> str:
        """
        Rule-based risk estimation — NOT a clinical diagnosis.
        Emergency symptoms always flag 'seek_urgent'.
        """
        # Emergency / urgent flags
        if (self.fainting == 'yes'
                or (self.chest_discomfort == 'yes' and self.chest_pain_level >= 7)
                or (self.shortness_of_breath == 'yes' and self.shortness_at_rest == 'yes')):
            return 'seek_urgent'

        score = 0
        if self.chest_discomfort in ('yes', 'sometimes'):
            score += self.chest_pain_level
        if self.shortness_of_breath in ('yes', 'sometimes'):
            score += 2
        if self.dizziness in ('yes', 'sometimes'):
            score += 1
        if self.palpitations in ('yes', 'sometimes'):
            score += 1
        if self.fatigue in ('yes', 'sometimes'):
            score += 1
        if self.swollen_ankles == 'yes':
            score += 1
        # Risk factors
        if self.smoker == 'yes':
            score += 1
        if self.diabetes == 'yes':
            score += 1
        if self.high_blood_pressure == 'yes':
            score += 1
        if self.family_heart_history == 'yes':
            score += 1
        # Age
        if self.age and self.age > 60:
            score += 2
        elif self.age and self.age > 45:
            score += 1

        if score <= 2:
            return 'low'
        elif score <= 6:
            return 'moderate'
        else:
            return 'high'
