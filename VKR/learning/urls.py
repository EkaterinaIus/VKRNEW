from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.modules_view, name='modules'),
    path('module/<str:task_type>/lessons/', views.lessons_list_view, name='lessons_list'),
    path('module/<str:task_type>/', views.lesson_view, name='lesson'),
    path('check-answer/', views.check_answer_view, name='check_answer'),
    path('placement-test/', views.placement_test_view, name='placement_test'),
    path('placement-test/submit/', views.placement_test_submit_view, name='placement_test_submit'),
]
