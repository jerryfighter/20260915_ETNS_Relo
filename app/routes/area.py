from flask import Blueprint, render_template, request, jsonify

from app.models.area import Area
from app.models.review import Review
from app.services.area_service import search_areas, area_summary
from app.services.review_service import filter_and_sort_reviews

area_bp = Blueprint("area", __name__)


@area_bp.route("/areas")
def search():
    query = request.args.get("q", "").strip()
    areas = search_areas(query)
    return render_template("area/search.html", query=query, areas=areas)


@area_bp.route("/areas/compare")
def compare():
    ids = request.args.get("ids", "")
    area_ids = [int(i) for i in ids.split(",") if i.strip().isdigit()][:3]
    areas = [Area.query.get(area_id) for area_id in area_ids]
    areas = [a for a in areas if a is not None]
    all_areas = Area.query.order_by(Area.name.asc()).all()
    return render_template("area/compare.html", areas=areas, all_areas=all_areas)


@area_bp.route("/areas/<int:area_id>")
def detail(area_id):
    area = Area.query.get_or_404(area_id)

    filters = {
        "family_type": request.args.get("family_type") or None,
        "work_location": request.args.get("work_location") or None,
        "verified_only": request.args.get("verified_only") == "1",
    }
    if request.args.get("has_children") in ("0", "1"):
        filters["has_children"] = request.args.get("has_children") == "1"
    if request.args.get("has_car") in ("0", "1"):
        filters["has_car"] = request.args.get("has_car") == "1"
    if request.args.get("min_rating"):
        filters["min_rating"] = int(request.args.get("min_rating"))

    sort = request.args.get("sort", "recent")
    reviews_query = filter_and_sort_reviews(Review.query.filter_by(area_id=area.id), filters, sort)
    reviews = reviews_query.all()

    return render_template(
        "area/detail.html",
        area=area,
        ratings=area.average_ratings(),
        reviews=reviews,
        filters=request.args,
        sort=sort,
    )


# ---- JSON API (section 28) ----


@area_bp.route("/api/areas")
def api_list_areas():
    areas = Area.query.order_by(Area.name.asc()).all()
    return jsonify([area_summary(a) for a in areas])


@area_bp.route("/api/areas/search")
def api_search_areas():
    query = request.args.get("q", "")
    areas = search_areas(query)
    return jsonify([area_summary(a) for a in areas])


@area_bp.route("/api/areas/<int:area_id>")
def api_get_area(area_id):
    area = Area.query.get_or_404(area_id)
    return jsonify(area_summary(area))
