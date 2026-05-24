from django.urls import path
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('child/add/', views.add_child_view, name='add_child'),
    path('child/select/', views.select_child_view, name='select_child'),
    path('child/<int:child_id>/delete/', views.delete_child_view, name='delete_child'),
    path('verify-access-code/', views.verify_access_code_view, name='verify_access_code'),
    path('check-access/', views.check_access_status_view, name='check_access'),
    path('reset-access-code/', views.reset_access_code_view, name='reset_access_code'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('child/<int:child_id>/edit/', views.edit_child_view, name='edit_child'),

    # Сброс пароля
    path('password-reset/',
         PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
         ),
         name='password_reset'),
    path('password-reset/done/',
         PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
