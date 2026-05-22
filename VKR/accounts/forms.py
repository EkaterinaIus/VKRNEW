from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Child


class ParentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Имя пользователя'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'


class ParentLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Имя пользователя'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})


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
