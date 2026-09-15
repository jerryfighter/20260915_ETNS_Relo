import json
from datetime import datetime, timezone

from app.extensions import db
from app.models.review import Review, ReviewHistory
from app.models.report import Report

RATING_FIELDS = [
    "overall_rating",
    "transportation_rating",
    "safety_rating",
    "daily_life_rating",
    "housing_rating",
    "education_rating",
    "expat_rating",
]

REVIEW_CONTENT_FIELDS = RATING_FIELDS + [
    "move_in_date",
    "move_out_date",
    "family_type",
    "has_children",
    "work_location",
    "has_car",
    "positive_comment",
    "negative_comment",
    "would_recommend",
    "additional_comment",
]

SORT_OPTIONS = {
    "recent": Review.created_at.desc(),
    "highest": Review.overall_rating.desc(),
    "lowest": Review.overall_rating.asc(),
    "helpful": Review.helpful_count.desc(),
    "verified": Review.is_verified.desc(),
}


def _serialize_for_history(review):
    data = {}
    for field in REVIEW_CONTENT_FIELDS:
        value = getattr(review, field)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        data[field] = value
    return json.dumps(data)


def create_review(user, area, data):
    review = Review(
        user_id=user.id,
        area_id=area.id,
        move_in_date=data["move_in_date"],
        move_out_date=data.get("move_out_date"),
        family_type=data["family_type"],
        has_children=data.get("has_children", False),
        work_location=data.get("work_location"),
        has_car=data.get("has_car", False),
        overall_rating=data["overall_rating"],
        transportation_rating=data["transportation_rating"],
        safety_rating=data["safety_rating"],
        daily_life_rating=data["daily_life_rating"],
        housing_rating=data["housing_rating"],
        education_rating=data["education_rating"],
        expat_rating=data["expat_rating"],
        positive_comment=data.get("positive_comment"),
        negative_comment=data.get("negative_comment"),
        would_recommend=data.get("would_recommend", True),
        additional_comment=data.get("additional_comment"),
    )
    db.session.add(review)
    db.session.commit()
    return review


def update_review(review, data, modified_by):
    previous_content = _serialize_for_history(review)
    for field in REVIEW_CONTENT_FIELDS:
        if field in data:
            setattr(review, field, data[field])
    db.session.add(
        ReviewHistory(review_id=review.id, modified_by=modified_by, previous_content=previous_content)
    )
    db.session.commit()
    return review


def delete_review(review):
    db.session.delete(review)
    db.session.commit()


def filter_and_sort_reviews(query, filters, sort="recent"):
    family_type = filters.get("family_type")
    if family_type:
        query = query.filter(Review.family_type == family_type)

    has_children = filters.get("has_children")
    if has_children is not None:
        query = query.filter(Review.has_children == has_children)

    has_car = filters.get("has_car")
    if has_car is not None:
        query = query.filter(Review.has_car == has_car)

    work_location = filters.get("work_location")
    if work_location:
        query = query.filter(Review.work_location.ilike(f"%{work_location}%"))

    min_rating = filters.get("min_rating")
    if min_rating:
        query = query.filter(Review.overall_rating >= min_rating)

    verified_only = filters.get("verified_only")
    if verified_only:
        query = query.filter(Review.is_verified.is_(True))

    order = SORT_OPTIONS.get(sort, SORT_OPTIONS["recent"])
    return query.order_by(order)


def report_review(review, user, reason, detail=None):
    report = Report(review_id=review.id, user_id=user.id, reason=reason, detail=detail)
    db.session.add(report)
    db.session.commit()
    return report


def verify_review(review, verified=True):
    review.is_verified = verified
    db.session.commit()
    return review
