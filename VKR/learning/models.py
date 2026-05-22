from django.db import models


class Letter(models.Model):
    value = models.CharField(max_length=2, unique=True, verbose_name='Буква')
    sound_url = models.CharField(max_length=200, blank=True)
    image_url = models.CharField(max_length=200, blank=True)
    order_num = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_num']
        verbose_name = 'Буква'
        verbose_name_plural = 'Буквы'

    def __str__(self):
        return self.value


class Syllable(models.Model):
    value = models.CharField(max_length=4, unique=True, verbose_name='Слог')
    sound_url = models.CharField(max_length=200, blank=True)
    image_url = models.CharField(max_length=200, blank=True)
    order_num = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_num']
        verbose_name = 'Слог'
        verbose_name_plural = 'Слоги'

    def __str__(self):
        return self.value


class Word(models.Model):
    value = models.CharField(max_length=20, unique=True, verbose_name='Слово')
    sound_url = models.CharField(max_length=200, blank=True)
    image_url = models.CharField(max_length=200, blank=True)
    order_num = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_num']
        verbose_name = 'Слово'
        verbose_name_plural = 'Слова'

    def __str__(self):
        return self.value


class Task(models.Model):
    TASK_TYPES = [
        ('letter', 'Буква'),
        ('syllable', 'Слог'),
        ('word', 'Слово'),
    ]

    title = models.CharField(max_length=200, verbose_name='Заголовок')
    task_type = models.CharField(max_length=10, choices=TASK_TYPES, verbose_name='Тип')
    question_text = models.CharField(max_length=200, verbose_name='Вопрос')
    content_text = models.CharField(max_length=50, verbose_name='Содержимое')
    correct_answer = models.CharField(max_length=100, verbose_name='Правильный ответ')
    options = models.JSONField(default=list, verbose_name='Варианты ответа')
    level = models.IntegerField(
        choices=[(1, 'Буквы'), (2, 'Слоги'), (3, 'Слова')],
        verbose_name='Уровень'
    )
    difficulty = models.IntegerField(default=1, verbose_name='Сложность')
    is_placement_test = models.BooleanField(default=False, verbose_name='Входное тестирование')
    order_num = models.IntegerField(default=0)
    hint_text = models.CharField(max_length=300, blank=True, verbose_name='Подсказка')

    class Meta:
        ordering = ['level', 'order_num']
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return f'[{self.get_task_type_display()}] {self.content_text}'
