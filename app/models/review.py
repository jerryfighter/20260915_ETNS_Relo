from datetime import datetime, timezone

from app.extensions import db

FAMILY_TYPES = ["Single", "Couple", "Family"]


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey("areas.id"), nullable=False)

    move_in_date = db.Column(db.Date, nullable=False)
    move_out_date = db.Column(db.Date, nullable=True)
    family_type = db.Column(db.String(20), nullable=False)
    has_children = db.Column(db.Boolean, nullable=False, default=False)
    work_location = db.Column(db.String(120), nullable=True)
    has_car = db.Column(db.Boolean, nullable=False, default=False)

    overall_rating = db.Column(db.Integer, nullable=False)
    transportation_rating = db.Column(db.Integer, nullable=False)
    safety_rating = db.Column(db.Integer, nullable=False)
    daily_life_rating = db.Column(db.Integer, nullable=False)
    housing_rating = db.Column(db.Integer, nullable=False)
    education_rating = db.Column(db.Integer, nullable=False)
    expat_rating = db.Column(db.Integer, nullable=False)

    positive_comment = db.Column(db.Text, nullable=True)
    negative_comment = db.Column(db.Text, nullable=True)
    would_recommend = db.Column(db.Boolean, nullable=False, default=True)
    additional_comment = db.Column(db.Text, nullable=True)

    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    helpful_count = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    history = db.relationship(
        "ReviewHistory", backref="review", lazy="dynamic", cascade="all, delete-orphan"
    )
    reports = db.relationship("Report", backref="review", lazy="dynamic", cascade="all, delete-orphan")

    def years_lived(self):
        end = self.move_out_date or datetime.now(timezone.utc).date()
        days = (end - self.move_in_date).days
        years = round(days / 365, 1)
        return years

    def stay_period_label(self):
        start_year = self.move_in_date.year
        end_year = self.move_out_date.year if self.move_out_date else "Present"
        return f"{start_year} - {end_year}"

    def family_label(self):
        if self.family_type == "Family":
            return "Family with children" if self.has_children else "Family"
        if self.family_type == "Couple":
            return "Couple with children" if self.has_children else "Couple"
        return "Single"

    def __repr__(self):
        return f"<Review {self.id} area={self.area_id} user={self.user_id}>"


class ReviewHistory(db.Model):
    __tablename__ = "review_history"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    modified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    previous_content = db.Column(db.Text, nullable=False)
    modified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
