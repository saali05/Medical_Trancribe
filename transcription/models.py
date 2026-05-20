from django.db import models
from django.contrib.auth.models import User


# ── Original models (kept for existing features) ──────────────────────────────

class AudioRecord(models.Model):
    doctor           = models.ForeignKey(User, on_delete=models.CASCADE)
    audio_file       = models.FileField(upload_to='audio/')
    uploaded_at      = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Audio by {self.doctor.username} at {self.uploaded_at}"


class Transcript(models.Model):
    audio          = models.OneToOneField(AudioRecord, on_delete=models.CASCADE)
    raw_text       = models.TextField()
    processed_text = models.TextField()
    created_at     = models.DateTimeField(auto_now_add=True)


class ClinicalDocument(models.Model):
    transcript     = models.OneToOneField(Transcript, on_delete=models.CASCADE)
    patient_name   = models.CharField(max_length=200, blank=True)
    chief_complaint = models.TextField(blank=True)
    history        = models.TextField(blank=True)
    examination    = models.TextField(blank=True)
    diagnosis      = models.TextField(blank=True)
    prescription   = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    follow_up      = models.TextField(blank=True)
    is_approved    = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ClinicalDoc #{self.pk} — {self.patient_name}"


# ── New Transcription model (used by upload & transcribe flow) ────────────────

class Transcription(models.Model):
    audio_file           = models.FileField(upload_to='audio/')
    patient_name         = models.CharField(max_length=255, blank=True, default='')
    created_at           = models.DateTimeField(auto_now_add=True)

    # Full conversation with speaker labels stored as JSON
    conversation_json    = models.JSONField(default=list, blank=True)

    # Structured medical fields
    chief_complaint      = models.TextField(blank=True, default='')
    present_illness      = models.TextField(blank=True, default='')
    diagnosis            = models.TextField(blank=True, default='')
    prescription         = models.TextField(blank=True, default='')
    treatment_plan       = models.TextField(blank=True, default='')
    follow_up            = models.TextField(blank=True, default='')
    vitals               = models.TextField(blank=True, default='')
    past_medical_history = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Transcription #{self.id} — {self.patient_name or 'Unknown'} — {self.created_at:%Y-%m-%d %H:%M}"