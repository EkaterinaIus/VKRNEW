from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('api/<int:child_id>/', views.progress_api, name='api'),
]
