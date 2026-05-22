import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from accounts.models import Child
from progress.models import LearningSession, TaskAttempt, Mistake
from .models import Task

MODULE_INFO = {
    'letter': {
        'name': 'Волшебная Азбука',
        'icon': '🔤',
        'desc': 'Учимся узнавать буквы',
        'level': 1,
        'color': 'primary',
    },
    'syllable': {
        'name': 'Слоговые Паровозики',
        'icon': '🚂',
        'desc': 'Читаем слоги',
        'level': 2,
        'color': 'success',
    },
    'word': {
        'name': 'Слова-Сюрпризы',
        'icon': '🎁',
        'desc': 'Читаем целые слова',
        'level': 3,
        'color': 'warning',
    },
}


def index(request):
    return render(request, 'index.html')


def modules_view(request):
    child_id = request.session.get('current_child_id')
    child = None
    if child_id:
        child = Child.objects.filter(id=child_id).first()

    if not child and request.user.is_authenticated:
        children = request.user.children.all()
        if children.count() == 1:
            child = children.first()
            request.session['current_child_id'] = child.id
        elif children.count() > 1:
            return redirect(f'/accounts/child/select/?next=/learning/')

    return render(request, 'learning/modules.html', {
        'modules': MODULE_INFO,
        'child': child,
    })


def _get_or_create_session(request, child, task_type):
    session_key = f'learning_session_{task_type}'
    session_id = request.session.get(session_key)
    if session_id:
        ls = LearningSession.objects.filter(id=session_id, ended_at__isnull=True).first()
        if ls:
            return ls
    if child:
        ls = LearningSession.objects.create(child=child, task_type=task_type)
        request.session[session_key] = ls.id
        return ls
    return None


def _get_next_task(request, child, task_type):
    level = child.level if child else 1
    type_to_level = {'letter': 1, 'syllable': 2, 'word': 3}
    query_level = type_to_level.get(task_type, 1)

    tasks = Task.objects.filter(
        task_type=task_type,
        level=query_level,
        is_placement_test=False,
    ).order_by('order_num')

    completed_key = f'completed_tasks_{task_type}'
    completed_ids = request.session.get(completed_key, [])

    for task in tasks:
        if task.id not in completed_ids:
            return task

    # All done — reset and cycle
    request.session[completed_key] = []
    return tasks.first()


def lesson_view(request, task_type):
    if task_type not in MODULE_INFO:
        return redirect('learning:modules')

    child_id = request.session.get('current_child_id')
    child = None
    if child_id:
        child = Child.objects.filter(id=child_id).first()

    task_id = request.GET.get('task_id')
    if task_id:
        task = Task.objects.filter(id=task_id, task_type=task_type).first()
    else:
        task = _get_next_task(request, child, task_type)

    if not task:
        messages.info(request, 'Задания для этого уровня ещё не добавлены.')
        return redirect('learning:modules')

    consecutive_errors = request.session.get(f'consecutive_errors_{task_type}', 0)
    show_hint = consecutive_errors >= 2

    # Shuffle options for display
    options = list(task.options)
    random.shuffle(options)

    return render(request, 'learning/lesson.html', {
        'task': task,
        'options': options,
        'task_type': task_type,
        'module': MODULE_INFO[task_type],
        'child': child,
        'show_hint': show_hint,
        'consecutive_correct': request.session.get(f'consecutive_correct_{task_type}', 0),
        'consecutive_errors': consecutive_errors,
    })


@require_POST
def check_answer_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad_request'}, status=400)

    task_id = data.get('task_id')
    answer = data.get('answer', '').strip().upper()
    task_type = data.get('task_type', 'letter')

    task = get_object_or_404(Task, id=task_id)
    is_correct = answer == task.correct_answer.strip().upper()

    child_id = request.session.get('current_child_id')
    child = Child.objects.filter(id=child_id).first() if child_id else None

    learning_session = _get_or_create_session(request, child, task_type)

    if child:
        attempt_num = TaskAttempt.objects.filter(child=child, task=task).count() + 1
        TaskAttempt.objects.create(
            child=child,
            task=task,
            session=learning_session,
            answer=answer,
            is_correct=is_correct,
            attempt_number=attempt_num,
        )
        if learning_session:
            if is_correct:
                learning_session.score += 1
            else:
                learning_session.mistakes_count += 1
            learning_session.save(update_fields=['score', 'mistakes_count'])

    # Update consecutive counters
    correct_key = f'consecutive_correct_{task_type}'
    error_key = f'consecutive_errors_{task_type}'

    if is_correct:
        consecutive_correct = request.session.get(correct_key, 0) + 1
        request.session[correct_key] = consecutive_correct
        request.session[error_key] = 0
        # Mark task as completed
        completed_key = f'completed_tasks_{task_type}'
        completed = request.session.get(completed_key, [])
        if task.id not in completed:
            completed.append(task.id)
            request.session[completed_key] = completed
    else:
        consecutive_errors = request.session.get(error_key, 0) + 1
        request.session[error_key] = consecutive_errors
        request.session[correct_key] = 0

        # Record mistake with suggested lessons
        if child:
            suggested = list(
                Task.objects.filter(
                    task_type=task_type,
                    content_text__in=[task.content_text, answer],
                    is_placement_test=False,
                ).values_list('id', flat=True)[:3]
            )
            Mistake.objects.create(
                child=child,
                task=task,
                wrong_value=answer,
                correct_value=task.correct_answer,
                mistake_type=task_type,
                suggested_task_ids=suggested,
            )

    consecutive_correct = request.session.get(correct_key, 0)
    consecutive_errors = request.session.get(error_key, 0)

    level_up = False
    level_down = False
    new_level = child.level if child else 1

    # R1: 5 correct in a row → level up
    if child and consecutive_correct >= 5 and child.level < 3:
        child.level += 1
        child.save(update_fields=['level'])
        request.session[correct_key] = 0
        request.session[f'completed_tasks_{task_type}'] = []
        level_up = True
        new_level = child.level

    # R2: 3 errors in a row → reset task list
    if consecutive_errors >= 3:
        request.session[f'completed_tasks_{task_type}'] = []
        request.session[error_key] = 0
        level_down = True

    show_hint = (not is_correct) and consecutive_errors >= 2

    # Build suggested lessons list
    suggested_lessons = []
    if not is_correct:
        confused = [task.content_text]
        if answer and len(answer) <= 4:
            confused.append(answer)
        related = Task.objects.filter(
            task_type=task_type,
            content_text__in=confused,
            is_placement_test=False,
        )[:3]
        for rt in related:
            suggested_lessons.append({
                'title': f'Урок: {rt.get_task_type_display()} «{rt.content_text}»',
                'url': f'/learning/module/{task_type}/?task_id={rt.id}',
            })

    next_task = _get_next_task(request, child, task_type)

    if is_correct:
        if level_up:
            msg = f'Великолепно! Ты перешёл на новый уровень — {child.get_level_display_name()}! 🎉'
        else:
            msg = 'Молодец! Правильно! 🌟'
    else:
        type_labels = {'letter': 'буква', 'syllable': 'слог', 'word': 'слово'}
        label = type_labels.get(task_type, 'ответ')
        msg = f'Не совсем. Правильный {label}: «{task.correct_answer}»'
        if confused and len(confused) > 1:
            msg = f'Ой! Ты перепутал {task.content_text} и {answer}. {msg}'

    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': task.correct_answer,
        'message': msg,
        'hint': task.hint_text if show_hint else '',
        'show_hint': show_hint,
        'level_up': level_up,
        'level_down': level_down,
        'new_level': new_level,
        'consecutive_correct': consecutive_correct,
        'consecutive_errors': consecutive_errors,
        'suggested_lessons': suggested_lessons,
        'next_task_id': next_task.id if next_task else None,
    })


def placement_test_view(request):
    child_id = request.session.get('placement_child_id')
    if not child_id:
        return redirect('accounts:add_child')
    child = get_object_or_404(Child, id=child_id)

    tasks = list(Task.objects.filter(is_placement_test=True).order_by('order_num'))
    if not tasks:
        # Fallback: pick random regular tasks
        tasks = list(Task.objects.filter(is_placement_test=False).order_by('?')[:10])

    return render(request, 'learning/placement_test.html', {
        'tasks': tasks,
        'child': child,
        'total': len(tasks),
    })


@require_POST
def placement_test_submit_view(request):
    child_id = request.session.get('placement_child_id')
    if not child_id:
        return JsonResponse({'error': 'no_child'}, status=400)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad_request'}, status=400)

    answers = data.get('answers', {})
    if not answers:
        return JsonResponse({'error': 'no_answers'}, status=400)

    task_ids = [int(k) for k in answers.keys()]
    tasks = {t.id: t for t in Task.objects.filter(id__in=task_ids)}

    correct = sum(
        1 for tid, ans in answers.items()
        if int(tid) in tasks and ans.strip().upper() == tasks[int(tid)].correct_answer.strip().upper()
    )
    total = len(tasks)
    percent = (correct / total * 100) if total > 0 else 0

    if percent < 20:
        level = 1
    elif percent <= 70:
        level = 2
    else:
        level = 3

    child = get_object_or_404(Child, id=child_id)
    child.level = level
    child.initial_level_source = 'test'
    child.save(update_fields=['level', 'initial_level_source'])

    request.session.pop('placement_child_id', None)
    request.session['current_child_id'] = child.id

    level_names = {1: 'Буквы', 2: 'Слоги', 3: 'Слова'}

    return JsonResponse({
        'correct': correct,
        'total': total,
        'percent': round(percent),
        'level': level,
        'level_name': level_names[level],
        'child_name': child.name,
        'redirect': '/learning/',
    })
