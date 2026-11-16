"""Sign-in, sign-out, lockout and password change."""

from fastapi.testclient import TestClient

from tests.conftest import login, make_user


def test_pages_require_sign_in(app):
    client = TestClient(app)
    for path in ("/", "/scan", "/cook", "/recipes", "/profile", "/pantry/1", "/recipes/1"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303 and response.headers["location"] == "/login", path
    assert client.get("/healthz").json() == {"status": "ok"}


def test_wrong_password_is_rejected(app):
    make_user("mei")
    client = TestClient(app)
    response = client.post("/login", data={"username": "mei", "password": "nope nope"})
    assert response.status_code == 401
    assert client.get("/", follow_redirects=False).status_code == 303


def test_sign_in_is_case_insensitive_and_sign_out_works(app):
    make_user("mei")
    client = login(app, " Mei ")
    assert client.get("/", follow_redirects=False).status_code == 200
    client.post("/logout")
    assert client.get("/", follow_redirects=False).status_code == 303


def test_lockout_after_repeated_failures(app):
    make_user("mei")
    client = TestClient(app)
    for _ in range(5):
        assert client.post("/login", data={"username": "mei", "password": "wrong"}).status_code == 401
    # even the right password is refused while locked
    assert client.post("/login", data={"username": "mei", "password": "correct horse"}).status_code == 429


def test_password_change_signs_out_other_devices(app):
    make_user("mei")
    phone, laptop = login(app, "mei"), login(app, "mei")
    response = phone.post("/profile/password", data={"current": "correct horse", "new": "a new password"})
    assert response.status_code == 200
    assert phone.get("/", follow_redirects=False).status_code == 200
    assert laptop.get("/", follow_redirects=False).status_code == 303
    assert login(app, "mei", "a new password")


def test_short_new_password_is_refused(app):
    make_user("mei")
    client = login(app, "mei")
    client.post("/profile/password", data={"current": "correct horse", "new": "short"})
    assert login(app, "mei", "correct horse")


def test_cross_site_posts_are_blocked(app):
    make_user("mei")
    client = login(app, "mei")
    response = client.post("/pantry", data={"name": "Eggs"}, headers={"origin": "https://evil.example"})
    assert response.status_code == 403
    same_site = client.post("/pantry", data={"name": "Eggs"}, headers={"origin": "http://testserver"})
    assert same_site.status_code == 200


def test_language_switch(app):
    client = TestClient(app)
    assert 'lang="en"' in client.get("/login").text
    client.post("/lang", data={"lang": "zh", "back": "/login"})
    assert 'lang="zh-Hans"' in client.get("/login").text
    # never redirects off-site
    response = client.post("/lang", data={"lang": "en", "back": "//evil.example"}, follow_redirects=False)
    assert response.headers["location"] == "/"
