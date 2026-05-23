from django.contrib import admin
from .models import Letter, Syllable, Word, Task


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ('value', 'order_num')
    ordering = ('order_num',)


@admin.register(Syllable)
class SyllableAdmin(admin.ModelAdmin):
    list_display = ('value', 'order_num')


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('value', 'order_num')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('content_text', 'task_type', 'task_subtype', 'lesson_number', 'order_num', 'level', 'is_placement_test')
    list_filter = ('task_type', 'task_subtype', 'level', 'is_placement_test')
    search_fields = ('content_text', 'correct_answer', 'title')
    ordering = ('task_type', 'lesson_number', 'order_num')
