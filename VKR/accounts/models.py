import hashlib
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    access_code_hash = models.CharField(max_length=128, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Родитель'
        verbose_name_plural = 'Родители'

    def set_access_code(self, code):
        salt = self.email.encode('utf-8')
        self.access_code_hash = hashlib.pbkdf2_hmac(
            'sha256', code.encode('utf-8'), salt, 100000
        ).hex()

    def check_access_code(self, code):
        if not self.access_code_hash:
            return False
        salt = self.email.encode('utf-8')
        test_hash = hashlib.pbkdf2_hmac(
            'sha256', code.encode('utf-8'), salt, 100000
        ).hex()
        return self.access_code_hash == test_hash


class Child(models.Model):
    LEVEL_CHOICES = [
        (1, 'Буквы'),
        (2, 'Слоги'),
        (3, 'Слова'),
    ]
    INITIAL_SOURCE = [
        ('manual', 'Вручную'),
        ('test', 'Тестирование'),
    ]

    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=100, verbose_name='Имя')
    age = models.IntegerField(verbose_name='Возраст')
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1, verbose_name='Уровень')
    initial_level_source = models.CharField(
        max_length=10, choices=INITIAL_SOURCE, default='manual'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ребёнок'
        verbose_name_plural = 'Дети'

    def __str__(self):
        return f'{self.name} (родитель: {self.parent.email})'

    def get_level_display_name(self):
        mapping = {1: 'Буквы', 2: 'Слоги', 3: 'Слова'}
        return mapping.get(self.level, 'Буквы')
