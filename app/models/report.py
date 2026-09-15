from datetime import datetime, timezone

from app.extensions import db

REPORT_REASONS = ["Spam", "Fake Review", "Offensive Content", "Incorrect Information", "Other"]
REPORT_STATUSES = ["pending", "resolved", "dismissed"]


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reason = db.Column(db.String(40), nullable=False)
    detail = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Report {self.id} review={self.review_id} reason={self.reason}>"
