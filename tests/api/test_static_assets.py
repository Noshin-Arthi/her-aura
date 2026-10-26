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


# Characters that only show up in this app when text was damaged: a wrong Windows encoding (cp1252), or a Python
# octal escape. Writing the CSS escape "\2713" (a tick) from Python produced "¹" + "3", because \271 is octal for it.
MOJIBAKE = "¹ÂÃâ�"


def test_app_files_have_no_mis_encoded_characters():
    app = STYLE.parents[1]
    damaged = [f"{p.relative_to(app)}:{n}" for p in app.rglob("*") if p.suffix in {".html", ".css", ".py", ".svg"}
               for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if any(c in line for c in MOJIBAKE)]
    assert damaged == []
