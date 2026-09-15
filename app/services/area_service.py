from app.extensions import db
from app.models.area import Area


def search_areas(query):
    if not query:
        return Area.query.order_by(Area.name.asc()).all()
    like = f"%{query}%"
    return (
        Area.query.filter(
            db.or_(
                Area.name.ilike(like),
                Area.city.ilike(like),
                Area.district.ilike(like),
            )
        )
        .order_by(Area.name.asc())
        .all()
    )


def get_area_or_none(area_id):
    return Area.query.get(area_id)


def create_area(data):
    area = Area(
        name=data["name"],
        city=data["city"],
        district=data.get("district"),
        description=data.get("description"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
    )
    db.session.add(area)
    db.session.commit()
    return area


def update_area(area, data):
    for field in ("name", "city", "district", "description", "latitude", "longitude"):
        if field in data:
            setattr(area, field, data[field])
    db.session.commit()
    return area


def delete_area(area):
    db.session.delete(area)
    db.session.commit()


def popular_areas(limit=6):
    return Area.query.order_by(Area.name.asc()).limit(limit).all()


def area_summary(area):
    ratings = area.average_ratings()
    return {
        "id": area.id,
        "name": area.name,
        "city": area.city,
        "district": area.district,
        "overall_rating": ratings["overall_rating"],
        "review_count": area.review_count(),
        "ratings": ratings,
    }
