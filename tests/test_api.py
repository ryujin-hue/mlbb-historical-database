"""Contract tests for the MLBB Historical Database API.

The critical invariant: the API MUST expose exactly 78 GET endpoints.
"""
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.data import load  # noqa: E402
from api.main import app, count_api_routes  # noqa: E402

client = TestClient(app)


def test_exactly_78_endpoints():
    """Hard contract: 78 API endpoints, no more, no less."""
    assert count_api_routes() == 78


def test_root_index():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["total_endpoints"] == 78
    assert body["name"] == "MLBB Historical Database API"


def test_health_and_version():
    assert client.get("/api/v1/health").json()["status"] == "ok"
    v = client.get("/api/v1/version").json()
    assert v["current_live_patch"].startswith("2.2.16")


def test_heroes_master():
    n = len(load("hero_master.csv"))
    r = client.get("/api/v1/heroes?limit=500").json()
    assert r["total"] == n
    hero = client.get("/api/v1/heroes/lancelot").json()["data"]
    assert hero["hero"] == "Lancelot"
    assert client.get("/api/v1/heroes/count").json()["data"]["total"] == n


def test_hero_changes():
    r = client.get("/api/v1/heroes/changes?limit=1000").json()
    assert r["total"] == len(load("hero_changes.csv"))
    r2 = client.get("/api/v1/heroes/changes/type/New?limit=1000").json()
    assert r2["total"] == sum(1 for x in load("hero_changes.csv")
                              if x["change_type"] == "New")


def test_items():
    assert client.get("/api/v1/items?limit=1000").json()["total"] == len(load("items_master.csv"))
    assert client.get("/api/v1/items/blade-of-despair").status_code == 200
    assert client.get("/api/v1/items/does-not-exist").status_code == 404


def test_patches():
    n = len(load("patch_index.csv"))
    r = client.get("/api/v1/patches?limit=1000").json()
    assert r["total"] == n
    latest = client.get("/api/v1/patches/latest").json()["data"]
    assert latest["version"].startswith("2.2.16")
    s = client.get("/api/v1/patches/2.2.16/summary").json()["data"]
    assert s["hero_change_count"] > 0


def test_mseries():
    r = client.get("/api/v1/mseries").json()
    assert r["total"] == 8
    m7 = client.get("/api/v1/mseries/m7").json()["data"]
    assert m7["champion"].startswith("Aurora Gaming PH")  # "Aurora Gaming PH (4-0)"
    vp = client.get("/api/v1/mseries/viewership").json()["data"]
    assert vp[0]["peak_viewers"] == 5680511  # M7 record


def test_esports():
    assert client.get("/api/v1/esports?limit=100").json()["total"] == len(load("esports.csv"))
    assert client.get("/api/v1/esports/region/Philippines").json()["total"] > 0


def test_systems_and_reference():
    assert client.get("/api/v1/systems?limit=200").json()["total"] == len(load("systems.csv"))
    assert client.get("/api/v1/systems/battle-spells").json()["total"] == \
        len(load("battle_spells.csv", ref=True))
    assert client.get("/api/v1/reference").json()["total"] >= 13
    assert client.get("/api/v1/reference/roles").status_code == 200
    assert client.get("/api/v1/reference/nope").status_code == 404


def test_client_business_extras():
    assert client.get("/api/v1/client?limit=100").json()["total"] == len(load("client.csv"))
    assert client.get("/api/v1/client/collabs").json()["total"] == \
        sum(1 for r in load("client.csv") if r["aspect"] == "Collab")
    assert client.get("/api/v1/business?limit=100").json()["total"] == len(load("business.csv"))
    assert client.get("/api/v1/business/ownership").json()["total"] == \
        sum(1 for r in load("business.csv") if r["topic"] == "Ownership")
    assert client.get("/api/v1/extras?limit=100").json()["total"] == len(load("heroes_extra.csv"))


def test_reports():
    r = client.get("/api/v1/reports/research_report").json()
    assert "57" in r["data"]["content"][:2000] or "coverage" in r["data"]["content"].lower()
    assert client.get("/api/v1/reports/missing_report").status_code == 404


# Representative example values for path parameters (openapi path templates).
EXAMPLES = {
    "role": "assassin", "lane": "jungle", "year": "2024", "hero": "lancelot",
    "change_type": "Buff", "version": "2.2.16", "item": "blade-of-despair",
    "edition": "m7", "region": "Philippines", "category": "Moniyan Empire",
    "aspect": "Collab", "topic": "Moonton", "system": "Spell",
    "report_name": "research_report", "table": "currencies",
}


def _example_path(template: str) -> str:
    """Fill openapi path-template params with representative values."""
    path = template
    for param in re.findall(r"\{(\w+)\}", template):
        if param == "region" and "lore-region" in path:
            path = path.replace(f"{{{param}}}", "moniyan")
        elif param == "year" and "patches" in path:
            path = path.replace(f"{{{param}}}", "2022")  # no 2024 rows in patch_index
        elif param == "category" and "items" in path:
            path = path.replace(f"{{{param}}}", "T1 Attack")
        else:
            path = path.replace(f"{{{param}}}", EXAMPLES.get(param, "lancelot"))
    if path.endswith("/search"):
        path += "?q=a"
    return path


def test_all_endpoints_respond():
    """Every documented endpoint must return 200 with a representative example."""
    templates = [p for p, ops in app.openapi()["paths"].items() if "get" in ops]
    for template in templates:
        url = _example_path(template)
        assert client.get(url).status_code == 200, f"endpoint failed: {url}"
    assert len(templates) == 78
