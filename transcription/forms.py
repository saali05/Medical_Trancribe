from django import forms
from .models import Transcription

class AudioUploadForm(forms.ModelForm):
    class Meta:
        model  = Transcription
        fields = ['audio_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['audio_file'].required = False  # ← ADD THIS