import io
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage as DjangoEmail
from accounts.models import Child
from progress.models import TaskAttempt, LearningSession, Mistake


def _require_access(request):
    return request.user.is_authenticated


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
        context['letter_stats']   = _calc_stats(attempts.filter(task__task_type='letter'))
        context['syllable_stats'] = _calc_stats(attempts.filter(task__task_type='syllable'))
        context['word_stats']     = _calc_stats(attempts.filter(task__task_type='word'))
        context['recent_attempts'] = (
            attempts.select_related('task').order_by('-timestamp')[:25]
        )
        context['mistakes'] = (
            Mistake.objects.filter(child=selected_child).order_by('-timestamp')[:15]
        )
        context['sessions'] = (
            LearningSession.objects.filter(child=selected_child).order_by('-started_at')[:10]
        )

    return render(request, 'reports/report.html', context)


def _find_cyrillic_font():
    """Возвращает путь к TTF-шрифту с кириллицей или None."""
    import os
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
        '/usr/share/fonts/ubuntu/Ubuntu-R.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        '/usr/share/fonts/noto/NotoSans-Regular.ttf',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _generate_pdf_bytes(child):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # ── Шрифт ────────────────────────────────────────────────────────────
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'
    font_path = _find_cyrillic_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('CyrFont', font_path))
            font_name = font_bold = 'CyrFont'
        except Exception:
            pass

    # ── Стили ─────────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    def style(size=10, bold=False, color=colors.black, align='LEFT', space_before=0, space_after=4):
        return ParagraphStyle(
            name='_',
            fontName=font_bold if bold else font_name,
            fontSize=size,
            textColor=color,
            alignment={'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}.get(align, 0),
            spaceAfter=space_after,
            spaceBefore=space_before,
            leading=size * 1.4,
        )

    story = []

    # Заголовок
    child_name = child.name if child else 'Ребёнок'
    story.append(Paragraph(f'Отчёт об успехах: {child_name}', style(18, bold=True, align='CENTER', space_after=6)))
    from datetime import datetime
    story.append(Paragraph(
        f'Сформировано: {datetime.now().strftime("%d.%m.%Y %H:%M")}',
        style(9, color=colors.grey, align='CENTER', space_after=14)
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#2196F3'), spaceAfter=12))

    if not child:
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    level_map = {1: 'Буквы', 2: 'Слоги', 3: 'Слова'}
    story.append(Paragraph(
        f'Ребёнок: <b>{child_name}</b> | Текущий уровень: <b>{level_map.get(child.level, "")}</b>',
        style(11, space_after=12)
    ))

    # ── Сводная таблица ───────────────────────────────────────────────────
    story.append(Paragraph('Успеваемость по разделам', style(12, bold=True, space_after=6)))

    attempts_all = TaskAttempt.objects.filter(child=child)
    summary_rows = [['Раздел', 'Верных', 'Ошибок', 'Всего', 'Точность']]
    for label, ttype in [('Буквы', 'letter'), ('Слоги', 'syllable'), ('Слова', 'word')]:
        qs = attempts_all.filter(task__task_type=ttype)
        total = qs.count()
        correct = qs.filter(is_correct=True).count()
        pct = round(correct / total * 100) if total > 0 else 0
        summary_rows.append([
            Paragraph(label, style(10, bold=True)),
            Paragraph(str(correct), style(10, color=colors.HexColor('#2e7d32'))),
            Paragraph(str(total - correct), style(10, color=colors.HexColor('#c62828'))),
            str(total),
            f'{pct}%',
        ])

    col_w = [4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm]
    tbl = Table(summary_rows, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#1976D2')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, -1), font_name),
        ('FONTSIZE',      (0, 0), (-1, 0), 10),
        ('FONTSIZE',      (0, 1), (-1, -1), 10),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 0), (0, -1), 'LEFT'),
        ('LEFTPADDING',   (0, 0), (0, -1), 10),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#E3F2FD')]),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#BBDEFB')),
        ('LINEBELOW',     (0, 0), (-1, 0), 1, colors.HexColor('#1565C0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── Последние попытки ─────────────────────────────────────────────────
    attempts = attempts_all.select_related('task').order_by('-timestamp')[:50]
    if attempts:
        story.append(Paragraph('Последние задания (до 50)', style(12, bold=True, space_after=6)))

        rows = [['№', 'Задание', 'Раздел', 'Ответ ребёнка', 'Итог', 'Дата']]
        for i, a in enumerate(attempts, 1):
            result_txt = 'ВЕРНО' if a.is_correct else 'ОШИБКА'
            result_col = colors.HexColor('#2e7d32') if a.is_correct else colors.HexColor('#c62828')
            rows.append([
                str(i),
                Paragraph(a.task.content_text, style(10, bold=True)),
                a.task.get_task_type_display(),
                a.answer or '—',
                Paragraph(result_txt, style(9, color=result_col, bold=True)),
                a.timestamp.strftime('%d.%m.%Y\n%H:%M'),
            ])

        col_w2 = [1*cm, 3.5*cm, 2.5*cm, 3*cm, 2*cm, 2.5*cm]
        tbl2 = Table(rows, colWidths=col_w2, repeatRows=1)
        tbl2.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#37474F')),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, -1), font_name),
            ('FONTSIZE',      (0, 0), (-1, 0), 9),
            ('FONTSIZE',      (0, 1), (-1, -1), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN',         (1, 1), (1, -1), 'LEFT'),
            ('ALIGN',         (3, 1), (3, -1), 'LEFT'),
            ('LEFTPADDING',   (1, 0), (1, -1), 6),
            ('LEFTPADDING',   (3, 0), (3, -1), 6),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#ECEFF1')]),
            ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#CFD8DC')),
            ('LINEBELOW',     (0, 0), (-1, 0), 1, colors.HexColor('#263238')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(tbl2)

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
        return JsonResponse(
            {'error': 'Укажите email в профиле (Личный кабинет → Редактировать профиль).'},
            status=400
        )

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
