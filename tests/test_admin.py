from tests.conftest import login


def test_normal_user_cannot_access_admin(client, normal_user):
    login(client, normal_user.email, "Password1!")
    resp = client.get("/admin/")
    assert resp.status_code == 403


def test_anonymous_cannot_access_admin(client):
    resp = client.get("/admin/", follow_redirects=True)
    assert b"Log In" in resp.data or b"Please log in" in resp.data


def test_admin_dashboard_access(client, admin_user):
    login(client, admin_user.email, "AdminPass1!")
    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert b"Admin Dashboard" in resp.data


def test_admin_verify_review(client, admin_user, review):
    login(client, admin_user.email, "AdminPass1!")
    resp = client.post(f"/admin/reviews/{review.id}/verify", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Verified Resident" in resp.data


def test_admin_delete_review(client, admin_user, review):
    login(client, admin_user.email, "AdminPass1!")
    resp = client.post(f"/admin/reviews/{review.id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Review deleted" in resp.data


def test_admin_suspend_user(client, admin_user, normal_user):
    login(client, admin_user.email, "AdminPass1!")
    resp = client.post(f"/admin/users/{normal_user.id}/suspend", follow_redirects=True)
    assert resp.status_code == 200
    assert b"has been suspended" in resp.data


def test_suspended_user_cannot_login(client, admin_user, normal_user):
    login(client, admin_user.email, "AdminPass1!")
    client.post(f"/admin/users/{normal_user.id}/suspend")
    client.get("/logout")

    resp = login(client, normal_user.email, "Password1!")
    assert b"suspended" in resp.data


def test_admin_reports_listing(client, admin_user, other_user, review):
    login(client, other_user.email, "Password1!")
    client.post(f"/reviews/{review.id}/report", data={"reason": "Spam"})
    client.get("/logout")

    login(client, admin_user.email, "AdminPass1!")
    resp = client.get("/admin/reports")
    assert resp.status_code == 200
    assert b"Spam" in resp.data


def test_admin_resolve_report(client, admin_user, other_user, review, db):
    from app.models.report import Report

    login(client, other_user.email, "Password1!")
    client.post(f"/reviews/{review.id}/report", data={"reason": "Spam"})
    client.get("/logout")

    report = Report.query.first()
    login(client, admin_user.email, "AdminPass1!")
    resp = client.post(f"/admin/reports/{report.id}/resolve", follow_redirects=True)
    assert b"marked as resolved" in resp.data
