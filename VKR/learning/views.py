import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from accounts.models import Child
from progress.models import LearningSession, TaskAttempt, Mistake
from .models import Task


def _get_section_progress(child, task_type):
    if child is None:
        return {'percent': 0, 'stars': 0, 'total': 0}
    total = Task.objects.filter(task_type=task_type, is_placement_test=False).count()
    if total == 0:
        return {'percent': 0, 'stars': 0, 'total': 0}
    stars = (
        TaskAttempt.objects
        .filter(child=child, task__task_type=task_type, task__is_placement_test=False, is_correct=True)
        .values('task')
        .distinct()
        .count()
    )
    return {
        'percent': round(stars / total * 100),
        'stars': stars,
        'total': total,
    }


def _is_module_unlocked(child, task_type, letter_pct=None, syllable_pct=None):
    if child is None:
        return True
    if task_type == 'letter':
        return True
    if task_type == 'syllable':
        if child.level >= 2:
            return True
        if letter_pct is None:
            letter_pct = _get_section_progress(child, 'letter')['percent']
        return letter_pct >= 100
    if task_type == 'word':
        if child.level >= 3:
            return True
        if syllable_pct is None:
            syllable_pct = _get_section_progress(child, 'syllable')['percent']
        return syllable_pct >= 70
    return True


MODULE_INFO = {
    'letter':   {'name': 'Волшебная Азбука',    'icon': '🔤', 'desc': 'Учимся узнавать буквы', 'level': 1, 'color': 'primary'},
    'syllable': {'name': 'Слоговые Паровозики', 'icon': '🚂', 'desc': 'Читаем слоги',          'level': 2, 'color': 'success'},
    'word':     {'name': 'Слова-Сюрпризы',      'icon': '🎁', 'desc': 'Читаем целые слова',    'level': 3, 'color': 'warning'},
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
            return redirect('/accounts/child/select/?next=/learning/')

    progress = {}
    access = {}
    if child:
        for t in ('letter', 'syllable', 'word'):
            progress[t] = _get_section_progress(child, t)
        access['letter']   = True
        access['syllable'] = _is_module_unlocked(child, 'syllable', letter_pct=progress['letter']['percent'])
        access['word']     = _is_module_unlocked(child, 'word', syllable_pct=progress['syllable']['percent'])
    else:
        for t in ('letter', 'syllable', 'word'):
            progress[t] = {'percent': 0, 'stars': 0, 'total': 0}
            access[t] = True

    modules_data = [
        {'type_key': t, **MODULE_INFO[t], 'progress': progress[t], 'unlocked': access[t]}
        for t in ('letter', 'syllable', 'word')
    ]

    return render(request, 'learning/modules.html', {
        'modules_data': modules_data,
        'child': child,
    })


def lessons_list_view(request, task_type):
    if task_type not in MODULE_INFO:
        return redirect('learning:modules')

    child_id = request.session.get('current_child_id')
    child = Child.objects.filter(id=child_id).first() if child_id else None

    # Если ребёнок уже на более высоком уровне — весь предыдущий раздел открыт полностью
    all_unlocked = False
    if child:
        if task_type == 'letter' and child.level >= 2:
            all_unlocked = True
        elif task_type == 'syllable' and child.level >= 3:
            all_unlocked = True

    lesson_numbers = list(
        Task.objects.filter(task_type=task_type, is_placement_test=False, lesson_number__gt=0)
        .values_list('lesson_number', flat=True)
        .distinct()
        .order_by('lesson_number')
    )

    lessons = []
    prev_completed = True  # первый урок всегда доступен

    for ln in lesson_numbers:
        tasks_in_lesson = Task.objects.filter(
            task_type=task_type, lesson_number=ln, is_placement_test=False
        )
        total_tasks = tasks_in_lesson.count()

        if child and total_tasks > 0:
            stars = (
                TaskAttempt.objects
                .filter(child=child, task__in=tasks_in_lesson, is_correct=True)
                .values('task')
                .distinct()
                .count()
            )
        else:
            stars = 0

        # Урок пройден при >= 2 звёздах из 3
        completed = (stars >= 2 and total_tasks > 0)
        # Доступен: весь раздел открыт ИЛИ предыдущий урок пройден
        available = all_unlocked or prev_completed

        lessons.append({
            'number':    ln,
            'stars':     stars,
            'total':     total_tasks,
            'completed': completed,
            'available': available,
        })

        prev_completed = completed

    return render(request, 'learning/lessons_list.html', {
        'task_type': task_type,
        'module':    MODULE_INFO[task_type],
        'lessons':   lessons,
        'child':     child,
    })


def _get_or_create_session(request, child, task_type):
    session_key = f'learning_session_{task_type}'
    session_id  = request.session.get(session_key)
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
    type_to_level = {'letter': 1, 'syllable': 2, 'word': 3}
    tasks = Task.objects.filter(
        task_type=task_type,
        level=type_to_level.get(task_type, 1),
        is_placement_test=False,
    ).order_by('lesson_number', 'order_num')

    completed_key = f'completed_tasks_{task_type}'
    completed_ids = request.session.get(completed_key, [])

    for task in tasks:
        if task.id not in completed_ids:
            return task

    request.session[completed_key] = []
    return tasks.first()


def lesson_view(request, task_type):
    if task_type not in MODULE_INFO:
        return redirect('learning:modules')

    child_id = request.session.get('current_child_id')
    child = Child.objects.filter(id=child_id).first() if child_id else None

    if child:
        letter_pct   = _get_section_progress(child, 'letter')['percent']
        syllable_pct = _get_section_progress(child, 'syllable')['percent']
        if not _is_module_unlocked(child, task_type, letter_pct=letter_pct, syllable_pct=syllable_pct):
            if task_type == 'syllable':
                messages.warning(request, '📚 Сначала выучи все буквы! Пройди Волшебную Азбуку на 100%.')
            elif task_type == 'word':
                messages.warning(request, '🚂 Сначала потренируйся в чтении слогов! Пройди Слоговые Паровозики на 70%.')
            return redirect('learning:modules')

    task_id             = request.GET.get('task_id')
    lesson_number_param = request.GET.get('lesson_number')
    task = None

    if task_id:
        task = Task.objects.filter(id=task_id, task_type=task_type).first()
    elif lesson_number_param:
        ln            = int(lesson_number_param)
        completed_ids = request.session.get(f'completed_tasks_{task_type}', [])
        lesson_tasks  = Task.objects.filter(
            task_type=task_type, lesson_number=ln, is_placement_test=False
        ).order_by('order_num')
        task = next((t for t in lesson_tasks if t.id not in completed_ids), None)
        if task is None and lesson_tasks.exists():
            return redirect('learning:lessons_list', task_type=task_type)
    else:
        task = _get_next_task(request, child, task_type)

    if not task:
        messages.info(request, 'Задания для этого уровня ещё не добавлены.')
        return redirect('learning:modules')

    task_errors = request.session.get(f'task_{task.id}_errors', 0)
    show_hint   = task_errors >= 1

    options = list(task.options)
    random.shuffle(options)

    if task.lesson_number > 0:
        lesson_tasks    = Task.objects.filter(
            task_type=task_type, lesson_number=task.lesson_number, is_placement_test=False
        ).order_by('order_num')
        tasks_in_lesson = lesson_tasks.count()
        task_position   = task.order_num
    else:
        tasks_in_lesson = 0
        task_position   = 0

    return render(request, 'learning/lesson.html', {
        'task':                task,
        'options':             options,
        'task_type':           task_type,
        'module':              MODULE_INFO[task_type],
        'child':               child,
        'show_hint':           show_hint,
        'task_errors':         task_errors,
        'consecutive_correct': request.session.get(f'consecutive_correct_{task_type}', 0),
        'consecutive_errors':  request.session.get(f'consecutive_errors_{task_type}', 0),
        'lesson_number':       task.lesson_number,
        'task_position':       task_position,
        'tasks_in_lesson':     tasks_in_lesson,
    })


@require_POST
def check_answer_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad_request'}, status=400)

    task_id   = data.get('task_id')
    answer    = data.get('answer', '').strip().upper()
    task_type = data.get('task_type', 'letter')

    task       = get_object_or_404(Task, id=task_id)
    is_correct = answer == task.correct_answer.strip().upper()

    child_id = request.session.get('current_child_id')
    child    = Child.objects.filter(id=child_id).first() if child_id else None

    learning_session = _get_or_create_session(request, child, task_type)

    if child:
        attempt_num = TaskAttempt.objects.filter(child=child, task=task).count() + 1
        TaskAttempt.objects.create(
            child=child, task=task, session=learning_session,
            answer=answer, is_correct=is_correct, attempt_number=attempt_num,
        )
        if learning_session:
            if is_correct:
                learning_session.score += 1
            else:
                learning_session.mistakes_count += 1
            learning_session.save(update_fields=['score', 'mistakes_count'])

    # ── Счётчик ошибок на текущее задание ────────────────────────────────
    task_error_key = f'task_{task.id}_errors'
    if is_correct:
        task_errors = 0
        request.session.pop(task_error_key, None)
    else:
        task_errors = request.session.get(task_error_key, 0) + 1
        request.session[task_error_key] = task_errors

    # 1-я ошибка → подсказка; 2-я ошибка → задание провалено
    show_hint   = (not is_correct) and task_errors >= 1
    task_failed = (not is_correct) and task_errors >= 2

    # ── Глобальные счётчики (R1 / R2) ────────────────────────────────────
    correct_key = f'consecutive_correct_{task_type}'
    error_key   = f'consecutive_errors_{task_type}'

    if is_correct:
        consecutive_correct = request.session.get(correct_key, 0) + 1
        request.session[correct_key] = consecutive_correct
        request.session[error_key]   = 0
        completed_key = f'completed_tasks_{task_type}'
        completed = request.session.get(completed_key, [])
        if task.id not in completed:
            completed.append(task.id)
            request.session[completed_key] = completed
    else:
        consecutive_errors = request.session.get(error_key, 0) + 1
        request.session[error_key]   = consecutive_errors
        request.session[correct_key] = 0

        if child and task_failed:
            suggested_ids = list(
                Task.objects.filter(
                    task_type=task_type,
                    content_text=task.content_text,
                    is_placement_test=False,
                ).exclude(id=task.id).values_list('id', flat=True)[:3]
            )
            Mistake.objects.create(
                child=child, task=task,
                wrong_value=answer, correct_value=task.correct_answer,
                mistake_type=task_type, suggested_task_ids=suggested_ids,
            )

    consecutive_correct = request.session.get(correct_key, 0)
    consecutive_errors  = request.session.get(error_key, 0)

    level_up   = False
    level_down = False
    new_level  = child.level if child else 1

    # R1: 5 верных подряд → уровень выше
    if child and consecutive_correct >= 5 and child.level < 3:
        child.level += 1
        child.save(update_fields=['level'])
        request.session[correct_key] = 0
        request.session[f'completed_tasks_{task_type}'] = []
        level_up  = True
        new_level = child.level

    # R2: 3 ошибки подряд → сброс списка выполненных
    if consecutive_errors >= 3:
        request.session[f'completed_tasks_{task_type}'] = []
        request.session[error_key] = 0
        level_down = True

    # ── Ссылки на повторение (только при task_failed) ────────────────────
    suggested_lessons = []
    if task_failed:
        confused = [task.content_text]
        if answer and len(answer) <= 4:
            confused.append(answer)
        related = Task.objects.filter(
            task_type=task_type,
            content_text__in=confused,
            is_placement_test=False,
        ).exclude(id=task.id)[:4]
        for rt in related:
            suggested_lessons.append({
                'title': f'«{rt.content_text}»',
                'url':   f'/learning/module/{task_type}/?task_id={rt.id}',
            })
        # Если нет похожих заданий — предложить текущий урок заново
        if not suggested_lessons and task.lesson_number > 0:
            suggested_lessons.append({
                'title': f'Урок {task.lesson_number} заново',
                'url':   f'/learning/module/{task_type}/?lesson_number={task.lesson_number}',
            })

    # ── Навигация к следующему заданию ───────────────────────────────────
    completed_ids    = request.session.get(f'completed_tasks_{task_type}', [])
    lesson_completed = False
    next_task        = None

    if task.lesson_number > 0:
        lesson_tasks = list(Task.objects.filter(
            task_type=task_type,
            lesson_number=task.lesson_number,
            is_placement_test=False,
        ).order_by('order_num'))

        if is_correct:
            # Следующее незавершённое задание в уроке
            next_task = next(
                (t for t in lesson_tasks if t.id not in completed_ids), None
            )
            if next_task is None:
                # Все задания в сессии пройдены — проверяем звёзды в БД (>= 2 из 3)
                if child:
                    lesson_task_ids = [t.id for t in lesson_tasks]
                    done_count = (
                        TaskAttempt.objects
                        .filter(child=child, task_id__in=lesson_task_ids, is_correct=True)
                        .values('task').distinct().count()
                    )
                    lesson_completed = (done_count >= 2)
                else:
                    lesson_completed = True
        else:
            if task_failed:
                # Задание провалено — пропускаем, переходим к следующему по порядку
                idx = next((i for i, t in enumerate(lesson_tasks) if t.id == task.id), -1)
                next_task = lesson_tasks[idx + 1] if idx + 1 < len(lesson_tasks) else None
                if next_task is None:
                    # Больше заданий нет — проверяем звёзды
                    if child:
                        lesson_task_ids = [t.id for t in lesson_tasks]
                        done_count = (
                            TaskAttempt.objects
                            .filter(child=child, task_id__in=lesson_task_ids, is_correct=True)
                            .values('task').distinct().count()
                        )
                        lesson_completed = (done_count >= 2)
                    else:
                        lesson_completed = True
            else:
                # Первая ошибка — повторить то же задание
                next_task = task
    else:
        next_task = _get_next_task(request, child, task_type)

    # ── Сообщение ────────────────────────────────────────────────────────
    if is_correct:
        if level_up:
            msg = f'Великолепно! Ты перешёл на новый уровень — {child.get_level_display_name()}! 🎉'
        else:
            msg = 'Молодец! Правильно! 🌟'
    else:
        type_labels = {'letter': 'буква', 'syllable': 'слог', 'word': 'слово'}
        label = type_labels.get(task_type, 'ответ')
        msg   = f'Правильный {label}: «{task.correct_answer}»'
        if task_failed:
            msg = f'Не беда! {msg}. Переходим дальше!'

    return JsonResponse({
        'is_correct':          is_correct,
        'correct_answer':      task.correct_answer,
        'message':             msg,
        'hint':                task.hint_text if (show_hint and task.hint_text) else '',
        'show_hint':           show_hint,
        'task_errors':         task_errors,
        'task_failed':         task_failed,
        'level_up':            level_up,
        'level_down':          level_down,
        'new_level':           new_level,
        'consecutive_correct': consecutive_correct,
        'consecutive_errors':  consecutive_errors,
        'suggested_lessons':   suggested_lessons,
        'lesson_completed':    lesson_completed,
        'next_task_id':        next_task.id if next_task else None,
    })


def placement_test_view(request):
    child_id = request.session.get('placement_child_id')
    if not child_id:
        return redirect('accounts:add_child')
    child = get_object_or_404(Child, id=child_id)

    tasks = list(Task.objects.filter(is_placement_test=True).order_by('order_num'))
    if not tasks:
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
    tasks    = {t.id: t for t in Task.objects.filter(id__in=task_ids)}

    correct = sum(
        1 for tid, ans in answers.items()
        if int(tid) in tasks
        and ans.strip().upper() == tasks[int(tid)].correct_answer.strip().upper()
    )
    total   = len(tasks)
    percent = (correct / total * 100) if total > 0 else 0

    level = 1 if percent < 20 else (2 if percent <= 70 else 3)

    child = get_object_or_404(Child, id=child_id)
    child.level = level
    child.initial_level_source = 'test'
    child.save(update_fields=['level', 'initial_level_source'])

    request.session.pop('placement_child_id', None)
    request.session['current_child_id'] = child.id

    level_names = {1: 'Буквы', 2: 'Слоги', 3: 'Слова'}
    return JsonResponse({
        'correct':    correct,
        'total':      total,
        'percent':    round(percent),
        'level':      level,
        'level_name': level_names[level],
        'child_name': child.name,
        'redirect':   '/learning/',
    })
