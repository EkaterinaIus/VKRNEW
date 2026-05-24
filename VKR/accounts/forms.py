from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User, Child


class ParentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru',
        })
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # username обязателен для AbstractUser — используем email-префикс
        base = self.cleaned_data['email'].split('@')[0][:140]
        user.username = base
        if commit:
            # Обеспечиваем уникальность username
            suffix = 1
            candidate = user.username
            while User.objects.filter(username=candidate).exists():
                candidate = f'{base}_{suffix}'
                suffix += 1
            user.username = candidate
            user.save()
        return user


class ParentLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль',
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email', '').strip().lower()
        password = cleaned.get('password', '')
        if email and password:
            self._user = authenticate(self.request, username=email, password=password)
            if self._user is None:
                raise forms.ValidationError('Неверный email или пароль. Попробуйте ещё раз.')
            if not self._user.is_active:
                raise forms.ValidationError('Аккаунт отключён.')
        return cleaned

    def get_user(self):
        return self._user


class ChildForm(forms.ModelForm):
    LEVEL_CHOICE = [
        ('manual_1', 'Только буквы (Уровень 1)'),
        ('manual_2', 'Слоги (Уровень 2)'),
        ('manual_3', 'Слова (Уровень 3)'),
        ('test', 'Пройти входное тестирование'),
    ]
    level_choice = forms.ChoiceField(
        choices=LEVEL_CHOICE,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Выбор уровня',
        initial='manual_1',
    )

    class Meta:
        model = Child
        fields = ('name', 'age')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя ребёнка'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 3, 'max': 10}),
        }


class AccessCodeSetForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '4–6 цифр',
            'pattern': '[0-9]{4,6}',
            'inputmode': 'numeric',
        }),
        label='Новый код доступа',
    )
    code_confirm = forms.CharField(
        max_length=6,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите код',
            'pattern': '[0-9]{4,6}',
            'inputmode': 'numeric',
        }),
        label='Подтверждение кода',
    )

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code', '')
        confirm = cleaned_data.get('code_confirm', '')
        if code and not code.isdigit():
            raise forms.ValidationError('Код должен состоять только из цифр.')
        if code and confirm and code != confirm:
            raise forms.ValidationError('Коды не совпадают.')
        return cleaned_data


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name':  'Фамилия',
            'email':      'Email',
        }


class EditChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ('name', 'age')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя ребёнка'}),
            'age':  forms.NumberInput(attrs={'class': 'form-control', 'min': 3, 'max': 12}),
        }
        labels = {
            'name': 'Имя ребёнка',
            'age':  'Возраст',
        }
