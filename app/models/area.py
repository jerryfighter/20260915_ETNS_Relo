from datetime import datetime, timezone

from app.extensions import db


class Area(db.Model):
    __tablename__ = "areas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    city = db.Column(db.String(120), nullable=False)
    district = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reviews = db.relationship("Review", backref="area", lazy="dynamic", cascade="all, delete-orphan")

    RATING_FIELDS = [
        "overall_rating",
        "transportation_rating",
        "safety_rating",
        "daily_life_rating",
        "housing_rating",
        "education_rating",
        "expat_rating",
    ]

    def average_ratings(self):
        reviews = self.reviews.all()
        result = {field: 0.0 for field in self.RATING_FIELDS}
        if not reviews:
            return result
        for field in self.RATING_FIELDS:
            values = [getattr(r, field) for r in reviews if getattr(r, field) is not None]
            result[field] = round(sum(values) / len(values), 1) if values else 0.0
        return result

    def review_count(self):
        return self.reviews.count()

    def verified_review_count(self):
        return self.reviews.filter_by(is_verified=True).count()

    def __repr__(self):
        return f"<Area {self.name}, {self.city}>"
