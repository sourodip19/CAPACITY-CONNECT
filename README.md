# Capacity Connect

Capacity Connect is a Django-based Digital Capacity Building and Learning Management Portal built as a BTech CSE academic project. It supports role-based learning workflows for administrators, trainers, and students.

## Features

- **Authentication & roles**: Custom user model with `ADMIN`, `TRAINER`, and `STUDENT` roles; student self-registration; admin-only trainer creation; login/logout/profile/password management.
- **Course management**: Trainers/admins create, edit, publish/archive, and delete courses; students browse published courses, search/filter, and view course details.
- **Enrollment**: Students enroll in published courses with duplicate-enrollment prevention.
- **Learning materials**: Trainers/admins add PDF uploads or external links per course; enrolled students access materials and mark them complete.
- **Quizzes**: Trainers/admins create quizzes and MCQ questions with answer options; students take a quiz once, receive automatic scoring, and review results.
- **Progress tracking**: Course progress is computed from completed materials and attempted published quizzes; enrollment status updates automatically; dashboards show learner progress.
- **Notifications**: In-app notifications for key events (enrollment, new material, quiz published, quiz submission) with read/mark-all-read support.
- **Responsive UI**: Bootstrap 5 based layout with role-aware dashboards.

## Tech Stack

- Python / Django 6.1.3
- SQLite for local development (default)
- PostgreSQL via `DATABASE_URL` for deployment
- Gunicorn + WhiteNoise for production serving
- Bootstrap 5 + Bootstrap Icons

## Project Structure

```text
accounts/        Custom user, profiles, auth, role dashboards
courses/         Course CRUD, discovery, enrollment
materials/       Learning materials and completion tracking
quizzes/         Quizzes, questions, attempts, scoring
progress/        Progress calculation services
notifications/   In-app notifications
core/            Shared views/context processors
config/          Django settings and root URLs
templates/       Django templates
static/          CSS/JS assets
```

## Local Setup

1. **Create and activate a virtual environment**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root (see `.env.example`):

   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
   # Optional PostgreSQL:
   # DATABASE_URL=postgres://user:password@host:5432/dbname
   ```

4. **Run migrations**

   ```powershell
   python manage.py migrate
   ```

5. **Create an admin/superuser**

   ```powershell
   python manage.py createsuperuser
   ```

6. **Run the development server**

   ```powershell
   python manage.py runserver
   ```

## Testing

Run checks and tests:

```powershell
python manage.py check
python manage.py test -v 1
```

## Deployment (Render)

The repository includes [render.yaml](render.yaml) and [build.sh](build.sh).

- Build command: `bash build.sh`
- Start command: `gunicorn config.wsgi:application`
- Required environment variables: `SECRET_KEY`, `DEBUG=false`, `DATABASE_URL` (Render Postgres), and optionally `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.
- `RENDER_EXTERNAL_HOSTNAME` is supported by settings for Render deployments.

`build.sh` installs dependencies, runs `collectstatic`, and applies migrations.

## Notes

- This project uses a custom user model (`accounts.User`); if switching from a pre-custom-user local DB, recreate the local SQLite database before migrating.
- Uploaded media files are stored in `media/` locally. For production, configure persistent media storage as needed.
