import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import User, Child
from .forms import (
    ParentRegistrationForm, ParentLoginForm,
    ChildForm, AccessCodeSetForm,
    EditProfileForm, EditChildForm,
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Добро пожаловать! Добавьте профиль ребёнка.')
            return redirect('accounts:dashboard')
    else:
        form = ParentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = ParentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
    else:
        form = ParentLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    request.session.pop('current_child_id', None)
    logout(request)
    return redirect('index')


@login_required
def dashboard_view(request):
    children = request.user.children.all()
    access_form = AccessCodeSetForm()

    if request.method == 'POST' and 'set_code' in request.POST:
        access_form = AccessCodeSetForm(request.POST)
        if access_form.is_valid():
            request.user.set_access_code(access_form.cleaned_data['code'])
            request.user.save()
            messages.success(request, 'Код доступа успешно установлен.')
            return redirect('accounts:dashboard')

    return render(request, 'accounts/dashboard.html', {
        'children': children,
        'access_form': access_form,
    })


@login_required
def add_child_view(request):
    if request.method == 'POST':
        form = ChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user
            level_choice = form.cleaned_data['level_choice']

            if level_choice == 'test':
                child.initial_level_source = 'test'
                child.level = 1
                child.save()
                request.session['placement_child_id'] = child.id
                return redirect('learning:placement_test')
            else:
                level_map = {'manual_1': 1, 'manual_2': 2, 'manual_3': 3}
                child.level = level_map.get(level_choice, 1)
                child.initial_level_source = 'manual'
                child.save()
                messages.success(
                    request,
                    f'Профиль {child.name} создан! Уровень: {child.get_level_display_name()}.'
                )
                return redirect('accounts:dashboard')
    else:
        form = ChildForm()
    return render(request, 'accounts/child_form.html', {'form': form})


@login_required
def select_child_view(request):
    children = request.user.children.all()
    if not children.exists():
        messages.info(request, 'Сначала добавьте профиль ребёнка.')
        return redirect('accounts:add_child')

    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        child = get_object_or_404(Child, id=child_id, parent=request.user)
        request.session['current_child_id'] = child.id
        next_url = request.POST.get('next', '/learning/')
        return redirect(next_url)

    return render(request, 'accounts/select_child.html', {
        'children': children,
        'next_url': request.GET.get('next', '/learning/'),
    })


@require_POST
def verify_access_code_view(request):
    """Проверяет код и возвращает success/fail. Код не запоминается в сессии."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'not_authenticated'})

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'bad_request'})

    code = data.get('code', '')

    if not request.user.access_code_hash:
        return JsonResponse({'success': True})

    if request.user.check_access_code(code):
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Неверный код'})


def check_access_status_view(request):
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'has_code': bool(
            request.user.is_authenticated and request.user.access_code_hash
        ),
        'verified': False,
    })


@login_required
def reset_access_code_view(request):
    """Генерирует новый 6-значный код, хеширует, сохраняет, отправляет на email."""
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        if not password:
            messages.error(request, 'Введите пароль от аккаунта.')
        elif request.user.check_password(password):
            import random as _random
            new_code = ''.join([str(_random.randint(0, 9)) for _ in range(6)])
            request.user.set_access_code(new_code)
            request.user.save(update_fields=['access_code_hash'])

            email_sent = False
            if request.user.email:
                try:
                    from django.core.mail import EmailMultiAlternatives
                    from django.conf import settings as _settings
                    text_body = (
                        f'Здравствуйте!\n\n'
                        f'Ваш новый код доступа для приложения «Читайка»:\n\n'
                        f'    {new_code}\n\n'
                        f'Используйте его при входе в родительские разделы.\n\n'
                        f'С уважением,\nприложение «Читайка»'
                    )
                    html_body = f'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f4ff;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f4ff;padding:40px 16px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" border="0"
           style="background:#fff;border-radius:16px;overflow:hidden;max-width:560px;width:100%;">
      <tr>
        <td style="background:linear-gradient(135deg,#2196F3 0%,#00BCD4 100%);padding:36px 40px;text-align:center;">
          <div style="font-size:44px;line-height:1;margin-bottom:10px;">📚</div>
          <h1 style="margin:0;color:#fff;font-size:26px;font-weight:700;">Читайка</h1>
          <p style="margin:6px 0 0;color:rgba(255,255,255,.8);font-size:14px;">Учимся читать вместе</p>
        </td>
      </tr>
      <tr>
        <td style="padding:40px 40px 32px;">
          <h2 style="margin:0 0 16px;color:#1a237e;font-size:20px;font-weight:700;">Новый код доступа</h2>
          <p style="margin:0 0 24px;color:#555;font-size:15px;line-height:1.7;">
            Здравствуйте!<br>
            Ваш новый код доступа для приложения <strong style="color:#1565C0;">«Читайка»</strong>:
          </p>
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td align="center" style="padding:8px 0 32px;">
              <div style="display:inline-block;background:#f0f7ff;border:2px dashed #2196F3;
                          border-radius:16px;padding:20px 48px;">
                <span style="font-size:38px;font-weight:700;letter-spacing:14px;color:#1565C0;">
                  {new_code}
                </span>
              </div>
            </td></tr>
          </table>
          <p style="margin:0 0 24px;color:#555;font-size:15px;line-height:1.7;">
            Используйте этот код при входе в родительские разделы приложения.
          </p>
          <hr style="border:none;border-top:1px solid #e8f0fe;margin:0 0 20px;">
          <p style="margin:0;color:#aaa;font-size:12px;line-height:1.6;">
            Если вы не запрашивали смену кода — немедленно смените пароль от аккаунта.
          </p>
        </td>
      </tr>
      <tr>
        <td style="background:#f8fbff;padding:20px 40px;text-align:center;border-top:1px solid #e8f0fe;">
          <p style="margin:0;color:#bbb;font-size:12px;">С уважением, приложение «Читайка»</p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>'''
                    msg = EmailMultiAlternatives(
                        subject='Ваш новый код доступа — Читайка',
                        body=text_body,
                        from_email=_settings.DEFAULT_FROM_EMAIL,
                        to=[request.user.email],
                    )
                    msg.attach_alternative(html_body, 'text/html')
                    msg.send(fail_silently=False)
                    email_sent = True
                except Exception:
                    pass

            if email_sent:
                messages.success(
                    request,
                    f'✅ Новый код доступа отправлен на {request.user.email}. Проверьте почту.'
                )
            else:
                messages.warning(
                    request,
                    f'✅ Новый код доступа установлен, но письмо не удалось отправить. '
                    f'Запомните код: {new_code}'
                )
            return redirect('accounts:dashboard')
        else:
            messages.error(request, '❌ Неверный пароль от аккаунта. Попробуйте ещё раз.')

    return render(request, 'registration/access_code_reset.html')


@login_required
def edit_profile_view(request):
    profile_form = EditProfileForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            profile_form = EditProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, '✅ Данные профиля обновлены.')
                return redirect('accounts:edit_profile')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, '🔑 Пароль успешно изменён.')
                return redirect('accounts:edit_profile')

    return render(request, 'accounts/edit_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


@login_required
def edit_child_view(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    form = EditChildForm(instance=child)

    if request.method == 'POST':
        form = EditChildForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Данные {child.name} обновлены.')
            return redirect('accounts:dashboard')

    return render(request, 'accounts/edit_child.html', {'form': form, 'child': child})


@login_required
def delete_child_view(request, child_id):
    child = get_object_or_404(Child, id=child_id, parent=request.user)
    if request.method == 'POST':
        name = child.name
        child.delete()
        if request.session.get('current_child_id') == child_id:
            request.session.pop('current_child_id', None)
        messages.success(request, f'Профиль {name} удалён.')
    return redirect('accounts:dashboard')
