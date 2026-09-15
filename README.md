# ExpatReview Korea

A Flask MVP web application where expats who have actually lived in a Korean neighborhood can
review it — helping other expats choose where to live based on real experience, not generic
real-estate listings.

## Features

- Email/password authentication (hashed passwords, session login via Flask-Login)
- Area search and detail pages with category ratings (transportation, safety, daily life,
  housing, education, expat-life convenience)
- Resident reviews with family composition, children, car ownership, work location, and
  move-in/move-out dates
- Review filtering (family type, children, car, work location, minimum rating, verified-only)
  and sorting (recent, highest, lowest, most helpful, verified residents)
- Review edit/delete (owner or admin only, enforced server-side) with a review history table
- Review reporting (Spam / Fake Review / Offensive Content / Incorrect Information / Other)
- Side-by-side comparison of up to 3 areas
- Simple rating-weighted area recommendation based on user priorities
- Admin dashboard: user management (suspend/activate), area management (CRUD), review
  management (Verified Resident approval, delete), and report triage
- JSON API for areas, reviews, and admin operations (see `app/routes/*.py`)
- Responsive Bootstrap 5 UI

## Tech Stack

Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Jinja2, Bootstrap 5, SQLite (dev) /
PostgreSQL-ready (via `DATABASE_URL`).

## Setup

```bash
cd expat-review
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
python seed.py    # creates instance/expat_review.db with demo areas/users/reviews
python run.py      # http://localhost:5050
```

Demo accounts (created by `seed.py`):

- Admin: `admin@expatreview.kr` / `Admin1234!`
- Reviewer: `reviewer1@example.com` / `Password1!` (also reviewer2 ... reviewer12)

## Tests

```bash
pytest
```

## Project Structure

```
expat-review/
  app/
    __init__.py            # app factory
    extensions.py          # db, migrate, login_manager
    models/                # User, Area, Review, ReviewHistory, Report
    routes/                # auth, main, area, review, admin blueprints (HTML + JSON API)
    services/               # area_service, review_service, recommendation_service
    templates/              # Jinja2 templates (base, index, auth/, area/, review/, admin/)
    static/                 # css/style.css, js/main.js
  tests/                   # pytest suite (auth, area, review, admin)
  config.py
  run.py
  seed.py
  requirements.txt
```

## Notes

- Personally identifying information (real name, company, address, phone, email) is never
  shown on public review pages — only an anonymized nationality-based profile
  (e.g. "American Expat") plus lifestyle facts (family type, work area, car ownership).
- All admin routes verify `current_user.is_admin` server-side; hiding UI elements is not relied
  upon for access control.
- Recommendation scoring is a simple weighted average over category ratings, not machine
  learning — see `app/services/recommendation_service.py`.
