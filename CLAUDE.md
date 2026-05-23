# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 4.2 web application for teaching reading to children aged 4–7. Russian-language, locale hardcoded to `ru-ru` / `Europe/Moscow`. Located in `VKR/`.

## Commands

```bash
cd VKR

# Run dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Load initial data (run in order)
python manage.py loaddata fixtures/letters.json
python manage.py loaddata fixtures/syllables.json
python manage.py loaddata fixtures/words.json
python manage.py loaddata fixtures/tasks.json

# Create superuser
python manage.py createsuperuser
```

No test suite or linting config exists in this project.

## Architecture

**Apps:**
- `accounts` — `User` (extends `AbstractUser`, adds `access_code_hash`) and `Child` (FK to User, has `level` 1/2/3 and `initial_level_source`)
- `learning` — `Letter`/`Syllable`/`Word` reference models, `Task` (exercises). Key `Task` fields: `task_type` (letter/syllable/word), `task_subtype` (audio_choice/keyboard/find_no_audio/compose/image_choice), `lesson_number` (1–30, 0 for placement tests), `order_num` (1–3 within lesson), `content_text` (what's shown big), `correct_answer`, `options` (JSONField list). Tasks are ordered by `lesson_number, order_num`. `lesson.html` dispatches to `_task_<subtype>.html` partials based on `task.task_subtype`.
- `progress` — `LearningSession`, `TaskAttempt`, `Mistake`; one JSON endpoint: `GET /progress/api/<child_id>/` returns per-type (letter/syllable/word) attempt counts and accuracy percent
- `reports` — read-only views over progress data, PDF export via reportlab (tries multiple system font paths for Cyrillic fallback); both views use a custom `_require_access()` guard that checks login **and** `access_code_verified` session flag

**Key flows:**

*Access code:* Parents set a 4–6 digit PIN stored as PBKDF2-HMAC-SHA256 hash in `User.access_code_hash` (salt derived from username, not random). Sidebar "protected" links (`data-target-url=...`) trigger a Bootstrap modal via `main.js`. The modal POSTs to `/accounts/verify-access-code/` (JSON) and sets `request.session['access_code_verified'] = True` on success.

*Learning session:* No login required. Current child is tracked via `request.session['current_child_id']`. Task progression state is stored entirely in session under keys suffixed by `task_type` (letter/syllable/word): `completed_tasks_<type>` (list of IDs), `consecutive_correct_<type>`, `consecutive_errors_<type>`, `learning_session_<type>` (active `LearningSession` PK). Counters reset if the session expires. Rules applied in `check_answer` view: 5 correct in a row → increment `child.level` and reset counters (R1); 3 errors in a row → reset completed-task list only (does **not** decrement `child.level`) and return `level_down: true` to the client (R2); 2+ consecutive errors → return `show_hint: true` so the next task renders `task.hint_text` (R3). Answer comparison is case-insensitive: `answer.strip().upper() == task.correct_answer.strip().upper()`.

*Task serving:* `GET /learning/module/<task_type>/` serves one task at a time; completed task IDs are stored in `request.session['completed_tasks_<type>']`. `POST /learning/check-answer/` (AJAX JSON) records a `TaskAttempt`, updates counters, applies rules, and returns `{is_correct, correct_answer, message, level_up, level_down, next_task_id, show_hint, suggested_lessons}`.

*Placement test:* 10 tasks with `is_placement_test=True`. Stored in session as `placement_child_id` (separate from `current_child_id` during test). Results submitted via AJAX to `/learning/placement-test/submit/`; score determines initial level (< 20% → 1, 20–70% → 2, > 70% → 3).

**Context processor** (`reading_project/context_processors.py`) injects `access_code_verified`, `has_access_code`, `current_child_id` into every template. JS reads these from the `DJANGO_CONTEXT` object (including `csrfToken`) injected as a `<script>` block in `base.html`.

**Frontend:** Bootstrap 5 + `static/js/main.js` (sidebar toggle, protected-link modal handler, active link highlighting). Single JS file — no build step.

**Child creation flow:** `ChildForm` exposes a `level_choice` radio field (`manual_1`/`manual_2`/`manual_3`/`test`). Choosing `test` saves a stub child, sets `request.session['placement_child_id']`, and redirects to the placement test; the test's submit view writes the computed level and transfers `placement_child_id` → `current_child_id`.

**Module display names** (defined in `learning/views.py::MODULE_INFO`): `letter` → "Волшебная Азбука" (level 1), `syllable` → "Слоговые Паровозики" (level 2), `word` → "Слова-Сюрпризы" (level 3).

**Module unlock logic** (`learning/views.py::_is_module_unlocked`): letter — always open; syllable — `child.level >= 2` OR `letter_pct == 100`; word — `child.level >= 3` OR `syllable_pct >= 70`. Progress (`_get_section_progress`) counts unique tasks with at least one correct `TaskAttempt`, no new model needed.

**Edit views:** `GET/POST /accounts/profile/edit/` (`edit_profile_view`) — two forms: `EditProfileForm` + Django's `PasswordChangeForm`. `GET/POST /accounts/child/<id>/edit/` (`edit_child_view`) — `EditChildForm` (name, age).

**Email report:** `GET /reports/send-email/?child_id=<id>` → generates PDF via `_generate_pdf_bytes(child)` and sends via `EmailMessage`. Requires `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` in `.env`; defaults to console backend in dev. Parent must have `user.email` set.

**Access code covers Logout:** the "Выйти" link in the sidebar is now a `protected-link` too, preventing the child from logging the parent out.

**Fonts:** Comfortaa + Fredoka One loaded from Google Fonts in `base.html`. CSS vars are in `style.css :root` — sidebar uses `linear-gradient(160deg, #2196F3, #00BCD4)`.

**Note:** `djangorestframework` is in `requirements.txt` but unused — no serializers or API viewsets exist.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # Edit DB credentials

# PostgreSQL
createdb reading_db             # or via psql

python manage.py makemigrations  # creates migrations for all apps (no migrations dirs exist yet)
python manage.py migrate

# If re-loading tasks after model changes:
python manage.py shell -c "from learning.models import Task; Task.objects.all().delete()"
python manage.py loaddata fixtures/letters.json fixtures/syllables.json fixtures/words.json fixtures/tasks.json
python manage.py createsuperuser
python manage.py runserver
```

**.env variables:** `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
