# from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import AudioRecord, Transcript, ClinicalDocument

@admin.register(AudioRecord)
class AudioRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'audio_file', 'uploaded_at']
    list_filter  = ['doctor', 'uploaded_at']

@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display  = ['id', 'audio', 'created_at']
    readonly_fields = ['raw_text', 'processed_text']

@admin.register(ClinicalDocument)
class ClinicalDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient_name', 'is_approved', 'created_at']
    list_filter  = ['is_approved']