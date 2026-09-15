from tests.conftest import login


def test_register_success(client):
    resp = client.post(
        "/register",
        data={
            "email": "new@example.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
            "nickname": "Newbie",
            "nationality": "British",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Account created" in resp.data or b"Log In" in resp.data


def test_register_password_mismatch(client):
    resp = client.post(
        "/register",
        data={
            "email": "mismatch@example.com",
            "password": "Password1!",
            "confirm_password": "Different1!",
            "nickname": "Mismatch",
        },
        follow_redirects=True,
    )
    assert b"Passwords do not match" in resp.data


def test_register_duplicate_email(client, normal_user):
    resp = client.post(
        "/register",
        data={
            "email": normal_user.email,
            "password": "Password1!",
            "confirm_password": "Password1!",
            "nickname": "Dupe",
        },
        follow_redirects=True,
    )
    assert b"already registered" in resp.data


def test_login_success(client, normal_user):
    resp = login(client, "user@example.com", "Password1!")
    assert b"Welcome back" in resp.data


def test_login_wrong_password(client, normal_user):
    resp = login(client, "user@example.com", "WrongPassword")
    assert b"Invalid email or password" in resp.data


def test_logout(client, normal_user):
    login(client, "user@example.com", "Password1!")
    resp = client.get("/logout", follow_redirects=True)
    assert b"logged out" in resp.data


def test_review_creation_requires_login(client, area):
    resp = client.get(f"/areas/{area.id}/reviews/new", follow_redirects=True)
    assert b"Log In" in resp.data or b"Please log in" in resp.data
