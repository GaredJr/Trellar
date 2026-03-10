from __future__ import annotations

import re

from app import DEMO_LOGIN_EMAIL, DEMO_LOGIN_PASSWORD, app


def _extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _login_and_get_csrf(client) -> str:
    login_html = client.get("/login").get_data(as_text=True)
    csrf = _extract_csrf(login_html)

    login_response = client.post(
        "/login",
        data={
            "csrf_token": csrf,
            "email": DEMO_LOGIN_EMAIL,
            "password": DEMO_LOGIN_PASSWORD,
            "next": "/",
        },
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    home_html = client.get("/").get_data(as_text=True)
    return _extract_csrf(home_html)


def test_protected_routes_require_login():
    with app.test_client() as client:
        page_response = client.get("/boards")
        assert page_response.status_code == 302
        assert "/login" in page_response.headers["Location"]

        api_response = client.post("/api/boards/create", json={"name": "Nope"})
        assert api_response.status_code == 401
        assert api_response.get_json()["error"] == "unauthorized"


def test_user_and_settings_persist_in_runtime_store():
    with app.test_client() as client:
        csrf = _login_and_get_csrf(client)

        user_response = client.post(
            "/user",
            data={
                "csrf_token": csrf,
                "display_name": "Runtime User",
                "email": "runtime@example.com",
                "about": "Runtime profile text",
            },
        )
        assert user_response.status_code == 200
        user_html = client.get("/user").get_data(as_text=True)
        assert "Runtime User" in user_html
        assert "runtime@example.com" in user_html

        settings_response = client.post(
            "/settings",
            data={
                "csrf_token": csrf,
                "workspace_name": "Runtime Workspace",
                "default_visibility": "workspace",
                "digest_frequency": "weekly",
                "channel": "#runtime",
                "card_template": "Runtime template",
            },
        )
        assert settings_response.status_code == 200
        settings_html = client.get("/settings").get_data(as_text=True)
        assert "Runtime Workspace" in settings_html
        assert "#runtime" in settings_html


def test_board_api_move_archive_restore_and_export():
    with app.test_client() as client:
        csrf = _login_and_get_csrf(client)
        headers = {"X-CSRF-Token": csrf}

        board_html = client.get("/boards/product-roadmap").get_data(as_text=True)
        card_id_match = re.search(r'data-card-id="([^"]+)"', board_html)
        assert card_id_match is not None
        card_id = card_id_match.group(1)

        move_response = client.post(
            "/api/boards/product-roadmap/cards/move",
            json={"card_id": card_id, "direction": "right"},
            headers=headers,
        )
        assert move_response.status_code == 200
        assert move_response.get_json()["ok"] is True

        archive_response = client.post(
            "/api/boards/product-roadmap/cards/archive",
            json={"card_id": card_id},
            headers=headers,
        )
        assert archive_response.status_code == 200
        assert archive_response.get_json()["ok"] is True

        restore_response = client.post(
            "/api/boards/product-roadmap/cards/restore",
            json={"card_id": card_id},
            headers=headers,
        )
        assert restore_response.status_code == 200
        assert restore_response.get_json()["ok"] is True

        export_response = client.get("/activity/export.csv")
        assert export_response.status_code == 200
        assert "text/csv" in export_response.headers["Content-Type"]
        csv_body = export_response.get_data(as_text=True)
        assert "timestamp,board,title" in csv_body


def test_board_and_card_creation_work_end_to_end():
    with app.test_client() as client:
        csrf = _login_and_get_csrf(client)
        headers = {"X-CSRF-Token": csrf}

        create_board_response = client.post(
            "/api/boards/create",
            json={"name": "QA Runtime Board", "description": "Created in backend test"},
            headers=headers,
        )
        assert create_board_response.status_code == 201
        create_data = create_board_response.get_json()
        assert create_data["ok"] is True
        assert create_data["slug"] == "qa-runtime-board"

        boards_html = client.get("/boards").get_data(as_text=True)
        assert "QA Runtime Board" in boards_html

        new_board_html = client.get("/boards/qa-runtime-board").get_data(as_text=True)
        assert "Created in backend test" in new_board_html

        create_card_response = client.post(
            "/api/boards/qa-runtime-board/cards/create",
            json={
                "title": "Runtime created card",
                "meta": "Test - 1h",
                "lane_index": 0,
            },
            headers=headers,
        )
        assert create_card_response.status_code == 201
        create_card_data = create_card_response.get_json()
        assert create_card_data["ok"] is True
        assert create_card_data["card"]["title"] == "Runtime created card"

        updated_board_html = client.get("/boards/qa-runtime-board").get_data(as_text=True)
        assert "Runtime created card" in updated_board_html
