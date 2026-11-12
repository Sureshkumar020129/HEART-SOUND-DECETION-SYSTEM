"""Heart analysis forms."""
from django import forms
from django.conf import settings
from .models import HeartSoundRecording


class AudioUploadForm(forms.ModelForm):
    class Meta:
        model = HeartSoundRecording
        fields = ['audio_file']
        widgets = {
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.wav,.flac,.mp3,.ogg,.aiff,audio/*',
                'id': 'audioFileInput',
            })
        }

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get('audio_file')
        if not audio_file:
            raise forms.ValidationError('Please select an audio file.')

        # Size check
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)
        if audio_file.size > max_size:
            max_mb = max_size // (1024 * 1024)
            raise forms.ValidationError(
                f'File is too large ({audio_file.size // (1024*1024)} MB). '
                f'Maximum allowed size is {max_mb} MB.'
            )

        # Extension check
        import os
        ext = os.path.splitext(audio_file.name)[1].lower()
        allowed = getattr(settings, 'ALLOWED_AUDIO_EXTENSIONS', ['.wav', '.flac', '.mp3', '.ogg'])
        if ext not in allowed:
            raise forms.ValidationError(
                f'Unsupported file format "{ext}". '
                f'Supported formats: {", ".join(allowed)}'
            )

        return audio_file
