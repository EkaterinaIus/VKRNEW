from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Child
from .models import LearningSession, TaskAttempt


@login_required
def progress_api(request, child_id):
    child = Child.objects.filter(id=child_id, parent=request.user).first()
    if not child:
        return JsonResponse({'error': 'not_found'}, status=404)

    attempts = TaskAttempt.objects.filter(child=child)
    data = {}
    for task_type in ('letter', 'syllable', 'word'):
        qs = attempts.filter(task__task_type=task_type)
        total = qs.count()
        correct = qs.filter(is_correct=True).count()
        data[task_type] = {
            'total': total,
            'correct': correct,
            'percent': round(correct / total * 100) if total > 0 else 0,
        }

    return JsonResponse({'child': child.name, 'level': child.level, 'stats': data})
