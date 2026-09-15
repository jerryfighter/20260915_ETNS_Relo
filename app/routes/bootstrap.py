"""One-time production data bootstrap.

Lets an already-deployed instance be seeded with demo data over HTTP,
without ever needing the raw database connection string outside of Vercel's
own environment variables. Protected by a random token so it can't be
triggered by anyone else. Intended to be removed once no longer needed.
"""
import os
import random
from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.user import User
from app.models.area import Area
from app.models.review import Review

bootstrap_bp = Blueprint("bootstrap", __name__)

AREAS = [
    {"name": "Gangnam", "city": "Seoul", "district": "Gangnam-gu",
     "description": "Upscale business and shopping district, popular with corporate expats."},
    {"name": "Pangyo", "city": "Seongnam", "district": "Bundang-gu",
     "description": "Korea's 'Silicon Valley' — tech campuses, new apartments, family-friendly."},
    {"name": "Bundang", "city": "Seongnam", "district": "Bundang-gu",
     "description": "Well-planned residential city known for schools and green spaces."},
    {"name": "Songdo", "city": "Incheon", "district": "Yeonsu-gu",
     "description": "Modern international business district with international schools."},
    {"name": "Itaewon", "city": "Seoul", "district": "Yongsan-gu",
     "description": "Historic international neighborhood, diverse food and nightlife."},
    {"name": "Hannam", "city": "Seoul", "district": "Yongsan-gu",
     "description": "Upscale residential area near embassies, popular with executives."},
]
NATIONALITIES = ["American", "British", "Canadian", "Australian", "German", "French", "Indian", "Japanese"]
WORK_LOCATIONS = ["Gangnam", "Pangyo", "Jongno", "Yeouido", "Seoul Station", "Songdo"]
FAMILY_TYPES = ["Single", "Couple", "Family"]
POSITIVE_COMMENTS = [
    "Great neighborhood for families, very safe at night.",
    "Excellent public transportation, commute was a breeze.",
    "Lots of international restaurants and grocery stores.",
    "Modern apartments with great amenities.",
    "Friendly neighbors and a strong expat community.",
    "Close to international schools, made the move much easier.",
]
NEGATIVE_COMMENTS = [
    "Rent is quite high compared to other areas.",
    "Can get crowded on weekends.",
    "Limited English signage in smaller shops.",
    "Parking is difficult to find.",
    "Far from the airport.",
    None,
]
TARGET_OVERALL = {"Gangnam": 4.3, "Pangyo": 4.4, "Bundang": 4.5, "Songdo": 4.1, "Itaewon": 4.0, "Hannam": 4.2}


def _rating_near(target):
    value = round(target + random.uniform(-0.6, 0.6))
    return max(1, min(5, value))


@bootstrap_bp.route("/_bootstrap/seed", methods=["POST"])
def seed():
    token = os.environ.get("SEED_TOKEN")
    if not token or request.headers.get("X-Seed-Token") != token:
        return jsonify({"error": "forbidden"}), 403

    if Area.query.count() > 0:
        return jsonify({"status": "skipped", "reason": "already seeded"}), 200

    random.seed(42)

    admin = User(email="admin@expatreview.kr", nickname="Admin", is_admin=True)
    admin.set_password("Admin1234!")
    db.session.add(admin)

    reviewers = []
    for i in range(1, 13):
        user = User(
            email=f"reviewer{i}@example.com",
            nickname=f"Reviewer{i}",
            nationality=random.choice(NATIONALITIES),
        )
        user.set_password("Password1!")
        db.session.add(user)
        reviewers.append(user)
    db.session.commit()

    areas = []
    for area_data in AREAS:
        area = Area(**area_data)
        db.session.add(area)
        areas.append(area)
    db.session.commit()

    review_total = 0
    for area in areas:
        target = TARGET_OVERALL.get(area.name, 4.2)
        for _ in range(random.randint(6, 10)):
            reviewer = random.choice(reviewers)
            move_in = date.today() - timedelta(days=random.randint(365, 365 * 4))
            move_out = None if random.random() < 0.4 else move_in + timedelta(days=random.randint(200, 900))
            db.session.add(
                Review(
                    user_id=reviewer.id,
                    area_id=area.id,
                    move_in_date=move_in,
                    move_out_date=move_out,
                    family_type=random.choice(FAMILY_TYPES),
                    has_children=random.random() < 0.4,
                    work_location=random.choice(WORK_LOCATIONS),
                    has_car=random.random() < 0.5,
                    overall_rating=_rating_near(target),
                    transportation_rating=_rating_near(target),
                    safety_rating=_rating_near(target + 0.2),
                    daily_life_rating=_rating_near(target - 0.1),
                    housing_rating=_rating_near(target - 0.1),
                    education_rating=_rating_near(target - 0.2),
                    expat_rating=_rating_near(target),
                    positive_comment=random.choice(POSITIVE_COMMENTS),
                    negative_comment=random.choice(NEGATIVE_COMMENTS),
                    would_recommend=random.random() < 0.85,
                    is_verified=random.random() < 0.5,
                )
            )
            review_total += 1
    db.session.commit()

    return jsonify({"status": "ok", "areas": len(areas), "users": len(reviewers) + 1, "reviews": review_total})
