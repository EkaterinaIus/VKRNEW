from django.db import models
from accounts.models import Child
from learning.models import Task


class LearningSession(models.Model):
    TASK_TYPES = [
        ('letter', 'Буква'),
        ('syllable', 'Слог'),
        ('word', 'Слово'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='sessions')
    task_type = models.CharField(max_length=10, choices=TASK_TYPES, default='letter')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    mistakes_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Сессия обучения'
        verbose_name_plural = 'Сессии обучения'

    def __str__(self):
        return f'{self.child.name} — {self.get_task_type_display()} — {self.started_at:%d.%m.%Y}'

    @property
    def total_attempts(self):
        return self.score + self.mistakes_count

    @property
    def accuracy(self):
        total = self.total_attempts
        return round(self.score / total * 100) if total > 0 else 0


class TaskAttempt(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attempts')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attempts')
    session = models.ForeignKey(
        LearningSession, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='attempts'
    )
    answer = models.CharField(max_length=100)
    is_correct = models.BooleanField()
    attempt_number = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Попытка ответа'
        verbose_name_plural = 'Попытки ответов'
        ordering = ['-timestamp']

    def __str__(self):
        result = '✓' if self.is_correct else '✗'
        return f'{self.child.name}: {self.task.content_text} → {self.answer} {result}'


class Mistake(models.Model):
    MISTAKE_TYPES = [
        ('letter', 'Буква'),
        ('syllable', 'Слог'),
        ('word', 'Слово'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='mistakes')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    wrong_value = models.CharField(max_length=50)
    correct_value = models.CharField(max_length=50)
    mistake_type = models.CharField(max_length=10, choices=MISTAKE_TYPES)
    suggested_task_ids = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ошибка'
        verbose_name_plural = 'Ошибки'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.child.name}: {self.wrong_value} вместо {self.correct_value}'
