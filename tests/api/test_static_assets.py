"""Static files: browsers must load the current stylesheet after a deploy, not an old cached copy."""
import hashlib
from pathlib import Path

STYLE = Path(__file__).resolve().parents[2] / "app" / "static" / "style.css"


def test_stylesheet_link_carries_a_content_version(client):
    version = hashlib.sha256(STYLE.read_bytes()).hexdigest()[:10]
    page = client.get("/")
    assert f'href="/static/style.css?v={version}"' in page.text


def test_versioned_stylesheet_is_served(client):
    response = client.get("/static/style.css?v=anything")
    assert response.status_code == 200 and "text/css" in response.headers["content-type"]
