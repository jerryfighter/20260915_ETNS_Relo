from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.area import Area
from app.models.review import Review
from app.models.report import Report
from app.services import area_service, review_service

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "user_count": User.query.count(),
        "area_count": Area.query.count(),
        "review_count": Review.query.count(),
        "verified_review_count": Review.query.filter_by(is_verified=True).count(),
        "pending_report_count": Report.query.filter_by(status="pending").count(),
    }
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(5).all()
    recent_reports = Report.query.filter_by(status="pending").order_by(Report.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, recent_reviews=recent_reviews, recent_reports=recent_reports)


@admin_bp.route("/users")
@admin_required
def users():
    query = request.args.get("q", "").strip()
    users_query = User.query
    if query:
        like = f"%{query}%"
        users_query = users_query.filter(db.or_(User.email.ilike(like), User.nickname.ilike(like)))
    all_users = users_query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, query=query)


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot suspend your own account.", "danger")
    else:
        user.is_active_user = False
        db.session.commit()
        flash(f"{user.nickname} has been suspended.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_user = True
    db.session.commit()
    flash(f"{user.nickname} has been reactivated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/areas")
@admin_required
def areas():
    all_areas = Area.query.order_by(Area.name.asc()).all()
    return render_template("admin/areas.html", areas=all_areas)


@admin_bp.route("/areas/new", methods=["POST"])
@admin_required
def create_area():
    data = {
        "name": request.form.get("name", "").strip(),
        "city": request.form.get("city", "").strip(),
        "district": request.form.get("district", "").strip() or None,
        "description": request.form.get("description", "").strip() or None,
        "latitude": request.form.get("latitude") or None,
        "longitude": request.form.get("longitude") or None,
    }
    if not data["name"] or not data["city"]:
        flash("Area name and city are required.", "danger")
    else:
        area_service.create_area(data)
        flash(f"Area '{data['name']}' created.", "success")
    return redirect(url_for("admin.areas"))


@admin_bp.route("/areas/<int:area_id>/edit", methods=["POST"])
@admin_required
def edit_area(area_id):
    area = Area.query.get_or_404(area_id)
    data = {
        "name": request.form.get("name", "").strip(),
        "city": request.form.get("city", "").strip(),
        "district": request.form.get("district", "").strip() or None,
        "description": request.form.get("description", "").strip() or None,
    }
    area_service.update_area(area, data)
    flash(f"Area '{area.name}' updated.", "success")
    return redirect(url_for("admin.areas"))


@admin_bp.route("/areas/<int:area_id>/delete", methods=["POST"])
@admin_required
def delete_area(area_id):
    area = Area.query.get_or_404(area_id)
    name = area.name
    area_service.delete_area(area)
    flash(f"Area '{name}' deleted.", "info")
    return redirect(url_for("admin.areas"))


@admin_bp.route("/reviews")
@admin_required
def reviews():
    status_filter = request.args.get("status", "all")
    reviews_query = Review.query
    if status_filter == "verified":
        reviews_query = reviews_query.filter_by(is_verified=True)
    elif status_filter == "unverified":
        reviews_query = reviews_query.filter_by(is_verified=False)
    all_reviews = reviews_query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=all_reviews, status_filter=status_filter)


@admin_bp.route("/reviews/<int:review_id>/verify", methods=["POST"])
@admin_required
def verify_review(review_id):
    review = Review.query.get_or_404(review_id)
    review_service.verify_review(review, True)
    flash("Review marked as Verified Resident.", "success")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reviews/<int:review_id>/unverify", methods=["POST"])
@admin_required
def unverify_review(review_id):
    review = Review.query.get_or_404(review_id)
    review_service.verify_review(review, False)
    flash("Verified Resident status removed.", "info")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    review_service.delete_review(review)
    flash("Review deleted.", "info")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reports")
@admin_required
def reports():
    status_filter = request.args.get("status", "pending")
    reports_query = Report.query
    if status_filter != "all":
        reports_query = reports_query.filter_by(status=status_filter)
    all_reports = reports_query.order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=all_reports, status_filter=status_filter)


@admin_bp.route("/reports/<int:report_id>/resolve", methods=["POST"])
@admin_required
def resolve_report(report_id):
    from datetime import datetime, timezone

    report = Report.query.get_or_404(report_id)
    report.status = "resolved"
    report.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Report marked as resolved.", "success")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/reports/<int:report_id>/dismiss", methods=["POST"])
@admin_required
def dismiss_report(report_id):
    from datetime import datetime, timezone

    report = Report.query.get_or_404(report_id)
    report.status = "dismissed"
    report.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Report dismissed.", "info")
    return redirect(url_for("admin.reports"))


# ---- JSON API (section 28) ----


@admin_bp.route("/api/users")
@admin_required
def api_users():
    return jsonify(
        [
            {
                "id": u.id,
                "email": u.email,
                "nickname": u.nickname,
                "nationality": u.nationality,
                "is_admin": u.is_admin,
                "is_active": u.is_active_user,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in User.query.order_by(User.created_at.desc()).all()
        ]
    )


@admin_bp.route("/api/reviews")
@admin_required
def api_reviews():
    return jsonify(
        [
            {
                "id": r.id,
                "area_id": r.area_id,
                "user_id": r.user_id,
                "overall_rating": r.overall_rating,
                "is_verified": r.is_verified,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in Review.query.order_by(Review.created_at.desc()).all()
        ]
    )


@admin_bp.route("/api/reports")
@admin_required
def api_reports():
    return jsonify(
        [
            {
                "id": rep.id,
                "review_id": rep.review_id,
                "reason": rep.reason,
                "status": rep.status,
                "created_at": rep.created_at.isoformat() if rep.created_at else None,
            }
            for rep in Report.query.order_by(Report.created_at.desc()).all()
        ]
    )


@admin_bp.route("/api/reviews/<int:review_id>/verify", methods=["PUT"])
@admin_required
def api_verify_review(review_id):
    review = Review.query.get_or_404(review_id)
    payload = request.get_json(force=True, silent=True) or {}
    review_service.verify_review(review, payload.get("verified", True))
    return jsonify({"id": review.id, "is_verified": review.is_verified})


@admin_bp.route("/api/reviews/<int:review_id>", methods=["DELETE"])
@admin_required
def api_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    review_service.delete_review(review)
    return "", 204
