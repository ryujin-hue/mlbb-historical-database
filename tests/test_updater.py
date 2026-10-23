"""Unit tests for the auto-update pipeline (parsers + merge logic).

Runs offline: uses fixture HTML snippets, no network access.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import update_data as upd  # noqa: E402


HEROES_ESCAPED = (
    '\\"heroes\\":[{\\"id\\":1,\\"slug\\":\\"lancelot\\",\\"name\\":\\"Lancelot\\",'
    '\\"role\\":[\\"Assassin\\"],\\"lane\\":[\\"Jungle\\"],\\"releaseYear\\":2017,'
    '\\"splashArt\\":\\"https://example.com/l.jpg\\"},'
    '{\\"id\\":2,\\"slug\\":\\"newhero\\",\\"name\\":\\"New Hero\\",'
    '\\"role\\":[\\"Mage\\",\\"Support\\"],\\"lane\\":[\\"Roam\\"],'
    '\\"releaseYear\\":2026,\\"splashArt\\":\\"\\"}]'
)


def test_parse_heroes():
    html = "<html>" + HEROES_ESCAPED + "</html>"
    heroes = upd.parse_heroes(html)
    assert len(heroes) == 2
    assert heroes[0]["name"] == "Lancelot"
    assert heroes[1]["role"] == ["Mage", "Support"]


def test_new_heroes_dedupes():
    known = [{"hero": "Lancelot"}]
    live = [
        {"name": "Lancelot", "slug": "lancelot"},
        {"name": "New Hero", "slug": "new-hero"},
    ]
    added = upd.new_heroes(live, known)
    assert [h["slug"] for h in added] == ["new-hero"]


def test_latest_patch():
    seg = ('\\"version\\":\\"2.2.17\\",\\"x\\":1 ... "released" '
           '\\"October 14, 2026\\"')
    version, date = upd.latest_patch(seg)
    assert version == "2.2.17"
    assert date == "2026-10-14"


def test_item_slugs():
    html = '\\"slug\\":\\"blade-of-despair\\" \\"slug\\":\\"war-axe\\" \\"slug\\":\\"war-axe\\"'
    assert upd.item_slugs(html) == {"blade-of-despair", "war-axe"}


def test_season_status():
    html = "MLBB Season 42 End Date ... December 16, 2026"
    s = upd.season_status(html)
    assert s["season"] == 42
    assert s["end_date"] == "2026-DEC-16"


def test_hero_rows_shape(tmp_path):
    h = {"name": "New Hero", "slug": "new-hero", "role": ["Mage"], "lane": ["Roam"],
         "releaseYear": 2026, "splashArt": ""}
    row = upd.hero_master_row(h, None)
    assert row["hero"] == "New Hero"
    assert row["role"] == "mage"
    assert "UNVERIFIED" in row["release_date"]
    assert row["image_path"] == "MISSING_IMAGE"
    ch = upd.hero_change_row(h, None)
    assert ch["change_type"] == "New"
    assert "auto-update" in ch["detail"]


def test_append_csv(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    upd.append_csv(f, [{"a": "3", "b": "4"}])
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    assert lines == ["a,b", "1,2", "3,4"]
