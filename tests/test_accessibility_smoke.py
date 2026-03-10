import re

from app import DEMO_LOGIN_EMAIL, DEMO_LOGIN_PASSWORD, app


def _extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _login(client) -> None:
    login_html = client.get("/login").get_data(as_text=True)
    csrf = _extract_csrf(login_html)
    response = client.post(
        "/login",
        data={
            "csrf_token": csrf,
            "email": DEMO_LOGIN_EMAIL,
            "password": DEMO_LOGIN_PASSWORD,
            "next": "/",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_core_routes_have_landmarks_and_skip_links():
    with app.test_client() as client:
        login_html = client.get("/login").get_data(as_text=True)
        assert "id=\"main-content\"" in login_html
        assert "id=\"site-nav\"" in login_html
        assert "Skip to main content" in login_html or "Hopp til hovedinnhold" in login_html

        _login(client)

        for path in [
            "/",
            "/boards",
            "/boards/product-roadmap",
            "/user",
            "/settings",
            "/activity",
            "/help",
        ]:
            response = client.get(path)
            assert response.status_code == 200
            html = response.get_data(as_text=True)
            assert "id=\"main-content\"" in html
            assert "id=\"site-nav\"" in html
            assert "Skip to main content" in html or "Hopp til hovedinnhold" in html


def test_forms_include_csrf_tokens():
    with app.test_client() as client:
        _login(client)
        html_user = client.get('/user').get_data(as_text=True)
        html_settings = client.get('/settings').get_data(as_text=True)

        assert 'name="csrf_token"' in html_user
        assert 'name="csrf_token"' in html_settings
