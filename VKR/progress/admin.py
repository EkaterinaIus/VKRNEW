from django.contrib import admin
from .models import LearningSession, TaskAttempt, Mistake


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ('child', 'task_type', 'score', 'mistakes_count', 'started_at')
    list_filter = ('task_type',)


@admin.register(TaskAttempt)
class TaskAttemptAdmin(admin.ModelAdmin):
    list_display = ('child', 'task', 'answer', 'is_correct', 'attempt_number', 'timestamp')
    list_filter = ('is_correct', 'task__task_type')


@admin.register(Mistake)
class MistakeAdmin(admin.ModelAdmin):
    list_display = ('child', 'wrong_value', 'correct_value', 'mistake_type', 'timestamp')
    list_filter = ('mistake_type',)
