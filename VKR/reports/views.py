import io
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage as DjangoEmail
from accounts.models import Child
from progress.models import TaskAttempt, LearningSession, Mistake


def _require_access(request):
    if not request.user.is_authenticated:
        return False
    if request.user.access_code_hash and not request.session.get('access_code_verified'):
        return False
    return True


def _calc_stats(attempts_qs):
    total = attempts_qs.count()
    correct = attempts_qs.filter(is_correct=True).count()
    return {
        'total': total,
        'correct': correct,
        'incorrect': total - correct,
        'percent': round(correct / total * 100) if total > 0 else 0,
    }


@login_required
def report_view(request):
    if not _require_access(request):
        return render(request, 'accounts/access_required.html', {
            'next_url': '/reports/',
            'section': 'Отчёт',
        })

    children = request.user.children.all()
    child_id = request.GET.get('child_id')
    selected_child = None

    if child_id:
        selected_child = children.filter(id=child_id).first()
    if not selected_child and children.exists():
        selected_child = children.first()

    context = {
        'children': children,
        'selected_child': selected_child,
    }

    if selected_child:
        attempts = TaskAttempt.objects.filter(child=selected_child)
        context['letter_stats'] = _calc_stats(attempts.filter(task__task_type='letter'))
        context['syllable_stats'] = _calc_stats(attempts.filter(task__task_type='syllable'))
        context['word_stats'] = _calc_stats(attempts.filter(task__task_type='word'))
        context['recent_attempts'] = (
            attempts.select_related('task').order_by('-timestamp')[:20]
        )
        context['mistakes'] = (
            Mistake.objects.filter(child=selected_child).order_by('-timestamp')[:10]
        )
        context['sessions'] = (
            LearningSession.objects.filter(child=selected_child).order_by('-started_at')[:10]
        )

    return render(request, 'reports/report.html', context)


def _generate_pdf_bytes(child):
    """Returns bytes of the PDF report for child, or raises Exception."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]
    font_name = 'Helvetica'
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('CyrillicFont', fp))
                font_name = 'CyrillicFont'
            except Exception:
                pass
            break

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    def P(text, style='Normal', **kw):
        s = styles[style].clone('tmp')
        s.fontName = font_name
        for k, v in kw.items():
            setattr(s, k, v)
        return Paragraph(text, s)

    child_name = child.name if child else 'Ребёнок'
    story.append(P(f'Отчёт об успехах: {child_name}', 'Title', fontSize=18))
    story.append(Spacer(1, 0.5*cm))

    if child:
        level_map = {1: 'Буквы', 2: 'Слоги', 3: 'Слова'}
        story.append(P(f'Текущий уровень: {level_map.get(child.level, "")}'))
        story.append(Spacer(1, 0.3*cm))

        # Stats per type
        attempts_all = TaskAttempt.objects.filter(child=child)
        for label, ttype in [('Буквы', 'letter'), ('Слоги', 'syllable'), ('Слова', 'word')]:
            qs = attempts_all.filter(task__task_type=ttype)
            total = qs.count()
            correct = qs.filter(is_correct=True).count()
            pct = round(correct / total * 100) if total > 0 else 0
            story.append(P(f'{label}: {correct}/{total} верно ({pct}%)'))
        story.append(Spacer(1, 0.4*cm))

        attempts = attempts_all.select_related('task').order_by('-timestamp')[:50]
        rows = [['Задание', 'Тип', 'Ответ', 'Итог', 'Дата']]
        for a in attempts:
            rows.append([
                a.task.content_text,
                a.task.get_task_type_display(),
                a.answer,
                'OK' if a.is_correct else 'X',
                a.timestamp.strftime('%d.%m.%Y %H:%M'),
            ])

        tbl = Table(rows, colWidths=[3*cm, 3*cm, 3*cm, 2*cm, 5*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#4A90D9')),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, -1), font_name),
            ('FONTSIZE',      (0, 0), (-1, 0), 10),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F4FF')]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ]))
        story.append(tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


@login_required
def export_pdf_view(request):
    if not _require_access(request):
        return HttpResponse('Доступ запрещён', status=403)

    child_id = request.GET.get('child_id')
    child = None
    if child_id:
        child = request.user.children.filter(id=child_id).first()
    if not child:
        child = request.user.children.first()

    try:
        pdf_bytes = _generate_pdf_bytes(child)
        name = child.name if child else 'child'
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{name}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f'Ошибка генерации PDF: {e}', status=500)


@login_required
def send_report_email_view(request):
    if not _require_access(request):
        return JsonResponse({'error': 'access_denied'}, status=403)

    if not request.user.email:
        return JsonResponse({'error': 'Укажите email в профиле (Личный кабинет → Редактировать профиль).'}, status=400)

    child_id = request.GET.get('child_id')
    child = None
    if child_id:
        child = request.user.children.filter(id=child_id).first()
    if not child:
        child = request.user.children.first()
    if not child:
        return JsonResponse({'error': 'Нет профиля ребёнка.'}, status=400)

    try:
        pdf_bytes = _generate_pdf_bytes(child)
        email = DjangoEmail(
            subject=f'Отчёт об успехах «{child.name}» — Читайка',
            body=(
                f'Здравствуйте!\n\n'
                f'Во вложении — отчёт об успехах {child.name} в приложении «Читайка».\n\n'
                f'Текущий уровень: {child.get_level_display_name()}.\n\n'
                f'С уважением,\nприложение «Читайка»'
            ),
            to=[request.user.email],
        )
        email.attach(f'report_{child.name}.pdf', pdf_bytes, 'application/pdf')
        email.send()
        return JsonResponse({'success': True, 'email': request.user.email})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
