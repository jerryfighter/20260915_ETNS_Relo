from datetime import date

import pytest

from app import create_app
from app.extensions import db as _db
from config import TestingConfig
from app.models.user import User
from app.models.area import Area
from app.models.review import Review


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def normal_user(db):
    user = User(email="user@example.com", nickname="Tester", nationality="American")
    user.set_password("Password1!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_user(db):
    user = User(email="other@example.com", nickname="OtherTester", nationality="Canadian")
    user.set_password("Password1!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db):
    user = User(email="admin@example.com", nickname="Admin", is_admin=True)
    user.set_password("AdminPass1!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def area(db):
    area = Area(name="Gangnam", city="Seoul", district="Gangnam-gu", description="Test area")
    db.session.add(area)
    db.session.commit()
    return area


@pytest.fixture
def review(db, normal_user, area):
    review = Review(
        user_id=normal_user.id,
        area_id=area.id,
        move_in_date=date(2023, 1, 1),
        move_out_date=None,
        family_type="Couple",
        has_children=False,
        work_location="Gangnam",
        has_car=True,
        overall_rating=4,
        transportation_rating=5,
        safety_rating=5,
        daily_life_rating=4,
        housing_rating=4,
        education_rating=4,
        expat_rating=4,
        positive_comment="Great area",
        negative_comment="A bit pricey",
        would_recommend=True,
    )
    db.session.add(review)
    db.session.commit()
    return review


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)
