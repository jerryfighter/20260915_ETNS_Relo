from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user

from app.models.area import Area
from app.models.review import Review
from app.models.report import REPORT_REASONS
from app.services import review_service

review_bp = Blueprint("review", __name__)

RATING_FIELDS = review_service.RATING_FIELDS


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _extract_review_form(form):
    data = {
        "move_in_date": _parse_date(form.get("move_in_date")),
        "move_out_date": _parse_date(form.get("move_out_date")),
        "family_type": form.get("family_type"),
        "has_children": form.get("has_children") == "on",
        "work_location": form.get("work_location", "").strip() or None,
        "has_car": form.get("has_car") == "on",
        "positive_comment": form.get("positive_comment", "").strip() or None,
        "negative_comment": form.get("negative_comment", "").strip() or None,
        "would_recommend": form.get("would_recommend") == "on",
        "additional_comment": form.get("additional_comment", "").strip() or None,
    }
    for field in RATING_FIELDS:
        value = form.get(field)
        data[field] = int(value) if value else None
    return data


def _validate_review_data(data):
    errors = []
    if data["move_in_date"] is None:
        errors.append("Move-in date is required.")
    if data["move_out_date"] and data["move_in_date"] and data["move_out_date"] < data["move_in_date"]:
        errors.append("Move-out date must be after move-in date.")
    if data["family_type"] not in ("Single", "Couple", "Family"):
        errors.append("Please select a valid family type.")
    for field in RATING_FIELDS:
        value = data.get(field)
        if value is None or not (1 <= value <= 5):
            errors.append("All rating fields must be between 1 and 5.")
            break
    return errors


@review_bp.route("/areas/<int:area_id>/reviews/new", methods=["GET", "POST"])
@login_required
def create(area_id):
    area = Area.query.get_or_404(area_id)

    if request.method == "POST":
        data = _extract_review_form(request.form)
        errors = _validate_review_data(data)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("review/create.html", area=area, form=request.form)

        review_service.create_review(current_user, area, data)
        flash("Thank you for sharing your experience!", "success")
        return redirect(url_for("area.detail", area_id=area.id))

    return render_template("review/create.html", area=area, form={})


@review_bp.route("/reviews/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        data = _extract_review_form(request.form)
        errors = _validate_review_data(data)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("review/edit.html", review=review, area=review.area, form=request.form)

        review_service.update_review(review, data, modified_by=current_user.id)
        flash("Your review has been updated.", "success")
        return redirect(url_for("area.detail", area_id=review.area_id))

    return render_template("review/edit.html", review=review, area=review.area, form={})


@review_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    area_id = review.area_id
    review_service.delete_review(review)
    flash("Review deleted.", "info")
    return redirect(url_for("area.detail", area_id=area_id))


@review_bp.route("/reviews/<int:review_id>/report", methods=["POST"])
@login_required
def report(review_id):
    review = Review.query.get_or_404(review_id)
    reason = request.form.get("reason")
    detail = request.form.get("detail", "").strip() or None

    if reason not in REPORT_REASONS:
        flash("Please select a valid report reason.", "danger")
        return redirect(url_for("area.detail", area_id=review.area_id))

    review_service.report_review(review, current_user, reason, detail)
    flash("Thank you. This review has been reported to our moderators.", "success")
    return redirect(url_for("area.detail", area_id=review.area_id))


# ---- JSON API (section 28) ----


@review_bp.route("/api/areas/<int:area_id>/reviews", methods=["GET"])
def api_list_reviews(area_id):
    Area.query.get_or_404(area_id)
    sort = request.args.get("sort", "recent")
    filters = {
        "family_type": request.args.get("family_type") or None,
        "verified_only": request.args.get("verified_only") == "1",
    }
    reviews = review_service.filter_and_sort_reviews(
        Review.query.filter_by(area_id=area_id), filters, sort
    ).all()
    return jsonify([_review_json(r) for r in reviews])


@review_bp.route("/api/areas/<int:area_id>/reviews", methods=["POST"])
@login_required
def api_create_review(area_id):
    area = Area.query.get_or_404(area_id)
    payload = request.get_json(force=True, silent=True) or {}
    data = {**payload}
    if data.get("move_in_date"):
        data["move_in_date"] = _parse_date(data["move_in_date"])
    if data.get("move_out_date"):
        data["move_out_date"] = _parse_date(data["move_out_date"])

    errors = _validate_review_data(
        {
            **data,
            **{f: data.get(f) for f in RATING_FIELDS},
        }
    )
    if errors:
        return jsonify({"errors": errors}), 400

    review = review_service.create_review(current_user, area, data)
    return jsonify(_review_json(review)), 201


@review_bp.route("/api/reviews/<int:review_id>", methods=["PUT"])
@login_required
def api_update_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    payload = request.get_json(force=True, silent=True) or {}
    if payload.get("move_in_date"):
        payload["move_in_date"] = _parse_date(payload["move_in_date"])
    if payload.get("move_out_date"):
        payload["move_out_date"] = _parse_date(payload["move_out_date"])

    review_service.update_review(review, payload, modified_by=current_user.id)
    return jsonify(_review_json(review))


@review_bp.route("/api/reviews/<int:review_id>", methods=["DELETE"])
@login_required
def api_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    review_service.delete_review(review)
    return "", 204


@review_bp.route("/api/reviews/<int:review_id>/report", methods=["POST"])
@login_required
def api_report_review(review_id):
    review = Review.query.get_or_404(review_id)
    payload = request.get_json(force=True, silent=True) or {}
    reason = payload.get("reason")
    if reason not in REPORT_REASONS:
        return jsonify({"error": "Invalid report reason."}), 400

    report_obj = review_service.report_review(review, current_user, reason, payload.get("detail"))
    return jsonify({"id": report_obj.id, "status": report_obj.status}), 201


def _review_json(review):
    return {
        "id": review.id,
        "area_id": review.area_id,
        "author": review.author.anonymized_profile(),
        "is_verified": review.is_verified,
        "family_type": review.family_label(),
        "has_car": review.has_car,
        "work_location": review.work_location,
        "stay_period": review.stay_period_label(),
        "ratings": {field: getattr(review, field) for field in RATING_FIELDS},
        "positive_comment": review.positive_comment,
        "negative_comment": review.negative_comment,
        "would_recommend": review.would_recommend,
        "additional_comment": review.additional_comment,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    }
