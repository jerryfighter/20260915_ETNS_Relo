from tests.conftest import login

VALID_REVIEW_FORM = {
    "move_in_date": "2023-01-01",
    "move_out_date": "",
    "family_type": "Couple",
    "has_children": "on",
    "work_location": "Gangnam",
    "has_car": "on",
    "overall_rating": "5",
    "transportation_rating": "5",
    "safety_rating": "5",
    "daily_life_rating": "4",
    "housing_rating": "4",
    "education_rating": "4",
    "expat_rating": "5",
    "positive_comment": "Loved it here",
    "negative_comment": "Rent is high",
    "would_recommend": "on",
    "additional_comment": "",
}


def test_create_review(client, normal_user, area):
    login(client, normal_user.email, "Password1!")
    resp = client.post(f"/areas/{area.id}/reviews/new", data=VALID_REVIEW_FORM, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Thank you for sharing" in resp.data
    assert b"Loved it here" in resp.data


def test_create_review_invalid_rating(client, normal_user, area):
    login(client, normal_user.email, "Password1!")
    bad_form = dict(VALID_REVIEW_FORM, overall_rating="9")
    resp = client.post(f"/areas/{area.id}/reviews/new", data=bad_form, follow_redirects=True)
    assert b"must be between 1 and 5" in resp.data


def test_edit_review_by_owner(client, normal_user, area, review):
    login(client, normal_user.email, "Password1!")
    updated_form = dict(VALID_REVIEW_FORM, positive_comment="Updated comment")
    resp = client.post(f"/reviews/{review.id}/edit", data=updated_form, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Updated comment" in resp.data


def test_edit_review_by_other_user_forbidden(client, other_user, review):
    login(client, other_user.email, "Password1!")
    resp = client.post(f"/reviews/{review.id}/edit", data=VALID_REVIEW_FORM)
    assert resp.status_code == 403


def test_delete_review_by_owner(client, normal_user, area, review):
    login(client, normal_user.email, "Password1!")
    resp = client.post(f"/reviews/{review.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Review deleted" in resp.data


def test_delete_review_by_other_user_forbidden(client, other_user, review):
    login(client, other_user.email, "Password1!")
    resp = client.post(f"/reviews/{review.id}/delete")
    assert resp.status_code == 403


def test_area_average_rating_calculation(app, db, area, normal_user):
    from datetime import date
    from app.models.review import Review

    for rating in (2, 4):
        db.session.add(
            Review(
                user_id=normal_user.id,
                area_id=area.id,
                move_in_date=date(2022, 1, 1),
                family_type="Single",
                has_children=False,
                has_car=False,
                overall_rating=rating,
                transportation_rating=rating,
                safety_rating=rating,
                daily_life_rating=rating,
                housing_rating=rating,
                education_rating=rating,
                expat_rating=rating,
            )
        )
    db.session.commit()
    ratings = area.average_ratings()
    assert ratings["overall_rating"] == 3.0


def test_review_filter_by_family_type(client, area, review):
    resp = client.get(f"/areas/{area.id}?family_type=Single")
    assert resp.status_code == 200
    assert b"Great area" not in resp.data


def test_review_sort_highest(client, area, review):
    resp = client.get(f"/areas/{area.id}?sort=highest")
    assert resp.status_code == 200


def test_report_review(client, other_user, review):
    login(client, other_user.email, "Password1!")
    resp = client.post(
        f"/reviews/{review.id}/report",
        data={"reason": "Spam", "detail": "Looks fake"},
        follow_redirects=True,
    )
    assert b"reported to our moderators" in resp.data
