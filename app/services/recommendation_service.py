from app.models.area import Area

PRIORITY_FIELDS = {
    "safety": "safety_rating",
    "transportation": "transportation_rating",
    "education": "education_rating",
    "housing": "housing_rating",
    "daily_life": "daily_life_rating",
    "expat_life": "expat_rating",
}

DEFAULT_WEIGHT = 1.0 / len(PRIORITY_FIELDS)
PRIORITY_WEIGHT_SHARE = 0.7
BASE_WEIGHT_SHARE = 0.3


def _build_weights(priorities):
    priorities = [p for p in priorities if p in PRIORITY_FIELDS]
    if not priorities:
        return {field: DEFAULT_WEIGHT for field in PRIORITY_FIELDS.values()}

    weights = {field: (BASE_WEIGHT_SHARE / len(PRIORITY_FIELDS)) for field in PRIORITY_FIELDS.values()}
    bonus = PRIORITY_WEIGHT_SHARE / len(priorities)
    for key in priorities:
        weights[PRIORITY_FIELDS[key]] += bonus
    return weights


def recommend_areas(priorities, limit=5):
    """Rating-weighted recommendation. `priorities` is a list of keys from PRIORITY_FIELDS."""
    weights = _build_weights(priorities)
    results = []
    for area in Area.query.all():
        if area.review_count() == 0:
            continue
        ratings = area.average_ratings()
        score = sum(ratings[field] * weight for field, weight in weights.items())
        match_score = round((score / 5.0) * 100, 1)
        results.append(
            {
                "area": area,
                "match_score": match_score,
                "ratings": ratings,
            }
        )
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results[:limit]
