from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from fastapi.testclient import TestClient

from app.auth.service import create_access_token
from app.main import app


def test_logout_expires_cookie_and_redirects_to_public_home():
    with TestClient(app) as client:
        client.cookies.set(
            "access_token",
            create_access_token({"sub": "00000000-0000-0000-0000-000000000000"}),
            domain="testserver.local",
            path="/",
        )
        before_logout = client.get("/api/auth/me")
        assert before_logout.json()["detail"] == "User not found"

        response = client.post("/api/auth/logout", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/"

        cookie_header = response.headers["set-cookie"]
        assert "access_token=" in cookie_header
        assert "Max-Age=0" in cookie_header
        assert "Path=/" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header
        assert "Secure" not in cookie_header

        cookie = parsedate_to_datetime(
            cookie_header.split("expires=", 1)[1].split(";", 1)[0]
        )
        assert cookie < datetime.now(timezone.utc)

        assert client.get("/").status_code == 200
        assert client.get("/api/auth/me").json()["detail"] == "Not authenticated"
        assert client.get("/api/wishlist/page").status_code == 401
