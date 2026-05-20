# transcription/urls.py  —  COMPLETE FILE (replace your existing one)
from .views import register_view
from django.urls import path
from . import views
from .views import download_pdf
from .views import download_docx


urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Upload / Record
    path('upload/', views.upload_audio, name='upload_audio'),

    # View & edit clinical document
    path('document/<int:pk>/', views.view_document, name='view_document'),

    
    # Export routes
    path('document/<int:pk>/export/pdf/',  views.export_pdf,  name='export_pdf'),
    path('document/<int:pk>/export/docx/', views.export_docx, name='export_docx'),
    # gpt
    path(
    'admin-dashboard/',
    views.admin_dashboard,
    name='admin_dashboard'
    ),

    path(
    'register/',
    register_view,
    name='register'
    ),

    path(
    'download-pdf/<int:pk>/',
    download_pdf,
    name='download_pdf'
    ),

    path(
    'download-docx/<int:pk>/',
    download_docx,
    name='download_docx'
    ),


    path('',              views.transcription_list,   name='transcription_list'),
    path('upload/',       views.upload_audio,         name='upload_audio'),
    path('<int:pk>/',     views.transcription_detail, name='transcription_detail'),

]