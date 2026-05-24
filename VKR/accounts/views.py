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
    """Сброс кода доступа по паролю от аккаунта."""
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        if not password:
            messages.error(request, 'Введите пароль от аккаунта.')
        elif request.user.check_password(password):
            request.user.access_code_hash = None
            request.user.save(update_fields=['access_code_hash'])
            messages.success(
                request,
                '✅ Код доступа сброшен. Установите новый в Личном кабинете.'
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
