from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_view, name='report'),
    path('export/pdf/', views.export_pdf_view, name='export_pdf'),
]
