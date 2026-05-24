# Настройка отправки email — Читайка

## Быстрый старт: Gmail

### Шаг 1. Включить двухфакторную аутентификацию
1. Зайдите в [myaccount.google.com](https://myaccount.google.com)
2. Безопасность → Двухэтапная аутентификация → Включить

### Шаг 2. Создать пароль приложения
1. Безопасность → **Пароли приложений** (появляется только после включения 2FA)
2. Выберите «Другое приложение» → введите «Читайка» → «Создать»
3. Скопируйте 16-значный пароль вида `xxxx xxxx xxxx xxxx`

### Шаг 3. Добавить переменные в `.env`

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

> Пробелы в пароле приложения можно оставить — Django их принимает.

---

## Тестирование

### В разработке (письма в терминал, ничего не отправляется)
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
Запустите сервер — письма будут выводиться в консоль.

### Быстрая проверка SMTP через Django shell
```bash
cd VKR
python manage.py shell
```
```python
from django.core.mail import send_mail
send_mail(
    subject='Тест — Читайка',
    message='Письмо отправлено успешно!',
    from_email=None,          # возьмёт DEFAULT_FROM_EMAIL из .env
    recipient_list=['your_email@gmail.com'],
)
```

### Проверка отправки отчёта через команду
```bash
python manage.py shell -c "
from reports.views import _generate_pdf_bytes
from accounts.models import Child
child = Child.objects.first()
pdf = _generate_pdf_bytes(child)
print(f'PDF сгенерирован: {len(pdf)} байт')
"
```

---

## Альтернативные SMTP-провайдеры

### Яндекс Почта
```env
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your_email@yandex.ru
EMAIL_HOST_PASSWORD=пароль_приложения
DEFAULT_FROM_EMAIL=your_email@yandex.ru
```
> Создать пароль приложения: Настройки → Безопасность → Пароли приложений

### Mail.ru
```env
EMAIL_HOST=smtp.mail.ru
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@mail.ru
EMAIL_HOST_PASSWORD=пароль_приложения
DEFAULT_FROM_EMAIL=your_email@mail.ru
```
> Включить «Внешние клиенты» в настройках почты Mail.ru

### Любой другой SMTP
```env
EMAIL_HOST=mail.yourhost.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourhost.com
EMAIL_HOST_PASSWORD=password
DEFAULT_FROM_EMAIL=noreply@yourhost.com
```

---

## Что отправляется в проекте

| Письмо | Откуда | Шаблоны |
|--------|--------|---------|
| Сброс пароля | `/accounts/password-reset/` | `registration/password_reset_email.html` (HTML) + `password_reset_email.txt` (plain text) |
| Новый код доступа | `/accounts/reset-access-code/` | Inline HTML в `accounts/views.py::reset_access_code_view` |
| PDF-отчёт | `/reports/send-email/` | Inline text в `reports/views.py::send_report_email_view` |

---

## Частые ошибки

**`SMTPAuthenticationError`** — неверный пароль приложения или не включена 2FA.

**`Connection refused`** — неверный HOST или PORT. Проверьте, не блокирует ли провайдер порт 587.

**`EMAIL_HOST_USER не задан`** — убедитесь, что `.env` загружается (файл в папке `VKR/`, рядом с `manage.py`).

**Письмо не приходит, но ошибок нет** — проверьте папку «Спам». Добавьте `DEFAULT_FROM_EMAIL` с отображаемым именем:
```env
DEFAULT_FROM_EMAIL=Читайка <noreply@gmail.com>
```
