from flask import Blueprint, render_template, request

from app.services.area_service import popular_areas, search_areas
from app.services.recommendation_service import recommend_areas, PRIORITY_FIELDS

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    query = request.args.get("q", "").strip()
    results = search_areas(query) if query else []
    return render_template(
        "index.html",
        query=query,
        results=results,
        popular=popular_areas(),
    )


@main_bp.route("/recommend", methods=["GET", "POST"])
def recommend():
    recommendations = None
    selected_priorities = []
    if request.method == "POST":
        selected_priorities = request.form.getlist("priorities")
        recommendations = recommend_areas(selected_priorities)
    return render_template(
        "recommend.html",
        priority_options=PRIORITY_FIELDS.keys(),
        selected_priorities=selected_priorities,
        recommendations=recommendations,
    )
