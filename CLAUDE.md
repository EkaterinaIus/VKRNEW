# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 4.2 web application for teaching reading to children aged 4–7. Located in `VKR/`.

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

## Architecture

**Apps:**
- `accounts` — `User` (extends `AbstractUser`, adds `access_code_hash`) and `Child` (FK to User, has `level` 1/2/3)
- `learning` — `Letter`/`Syllable`/`Word` reference models, `Task` (the actual exercises)
- `progress` — `LearningSession`, `TaskAttempt`, `Mistake` (records every answer)
- `reports` — read-only views over progress data, PDF export via reportlab

**Key flows:**

*Access code:* Parents set a 4–6 digit PIN stored as PBKDF2 hash in `User.access_code_hash`. Sidebar "protected" links (`data-target-url=...`) trigger a Bootstrap modal via `main.js`. The modal POSTs to `/accounts/verify-access-code/` (JSON) and sets `request.session['access_code_verified'] = True` on success.

*Learning session:* No login required. Current child is tracked via `request.session['current_child_id']`. Task progression state (consecutive correct/errors) is stored in session as `consecutive_correct_<type>` and `consecutive_errors_<type>`. Rules: 5 correct → level up (R1), 3 errors → reset task list (R2), 2 errors → show hint (R3).

*Task serving:* `GET /learning/module/<task_type>/` serves one task at a time; completed task IDs are stored in `request.session['completed_tasks_<type>']`. `POST /learning/check-answer/` (AJAX JSON) records a `TaskAttempt`, updates counters, applies rules, and returns the next task ID.

*Placement test:* 10 tasks with `is_placement_test=True`. Results submitted via AJAX to `/learning/placement-test/submit/`; score determines initial level (< 20% → 1, 20–70% → 2, > 70% → 3).

**Context processor** (`reading_project/context_processors.py`) injects `access_code_verified`, `has_access_code`, `current_child_id` into every template. JS reads these from `DJANGO_CONTEXT` object injected in `base.html`.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # Edit DB credentials

# PostgreSQL
createdb reading_db             # or via psql

python manage.py migrate
python manage.py loaddata fixtures/letters.json fixtures/syllables.json fixtures/words.json fixtures/tasks.json
python manage.py createsuperuser
python manage.py runserver
```

**.env variables:** `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
