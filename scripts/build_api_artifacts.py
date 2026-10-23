#!/usr/bin/env python3
"""Build API artifacts: static JSON mirror (78 files), openapi.json, API.md,
static index page and references/README.md. Run from anywhere.

Endpoint enumeration uses the generated OpenAPI schema — the stable contract —
instead of introspecting app.routes, so this works on every FastAPI version
(including >= 0.160 / Starlette 1.x, where included routers stay nested)."""
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app, count_api_routes  # noqa: E402

STATIC = REPO / "api" / "static" / "v1"

EXAMPLES = {
    "role": "assassin", "lane": "jungle", "year": "2024", "hero": "lancelot",
    "change_type": "Buff", "version": "2.2.16", "item": "blade-of-despair",
    "edition": "m7", "region": "Philippines", "category": "Moniyan Empire",
    "aspect": "Collab", "topic": "Moonton", "system": "Spell",
    "report_name": "research_report", "table": "currencies",
}


# ---------------- openapi-derived endpoint catalog ----------------
_spec = app.openapi()
GET_PATHS: list[str] = [p for p, ops in _spec["paths"].items() if "get" in ops]
GET_TAG = {p: (_spec["paths"][p]["get"].get("tags") or ["other"])[0] for p in GET_PATHS}
GET_SUMMARY = {p: _spec["paths"][p]["get"].get("summary", "") for p in GET_PATHS}


def example_path(template: str) -> str:
    path = template
    for param in re.findall(r"\{(\w+)\}", template):
        if param == "region" and "lore-region" in path:
            path = path.replace(f"{{{param}}}", "moniyan")
        elif param == "year" and "patches" in path:
            path = path.replace(f"{{{param}}}", "2022")
        elif param == "category" and "items" in path:
            path = path.replace(f"{{{param}}}", "T1 Attack")
        else:
            path = path.replace(f"{{{param}}}", EXAMPLES.get(param, "lancelot"))
    if path.endswith("/search"):
        path += "?q=a"
    return path


def static_name(path: str) -> str:
    name = path.replace("/", "_").strip("_").replace(" ", "_")
    return (name or "root") + ".json"


client = TestClient(app)
n = count_api_routes()
assert n == 78, f"expected 78 endpoints, got {n}"
print(f"endpoint count verified: {n}/78")

# sanity: the 78 endpoints must map to 78 UNIQUE static files
_names = [static_name(example_path(p)) for p in GET_PATHS]
assert len(set(_names)) == 78, "static mirror filenames are not unique"

# ---------------- openapi.json ----------------
spec = client.get("/openapi.json").json()
(REPO / "api" / "openapi.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
print(f"api/openapi.json written ({len(spec['paths'])} paths)")

# ---------------- static JSON mirror ----------------
if STATIC.exists():
    shutil.rmtree(STATIC)
STATIC.mkdir(parents=True)
failures, built = [], []
for template in GET_PATHS:
    url = example_path(template)
    r = client.get(url)
    if r.status_code != 200:
        failures.append((template, r.status_code))
        continue
    body = r.json()
    fname = static_name(url.split("?")[0])
    (STATIC / fname).write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
    built.append((template, fname))
if failures:
    raise SystemExit(f"static mirror failures: {failures}")
print(f"api/static/v1: {len(built)} JSON files")

# ---------------- static index.html ----------------
rows = "\n".join(
    f'<li><a href="v1/{f}"><code>GET {p}</code></a></li>' for p, f in built)
html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>MLBB Historical Database — Static API (78 endpoints)</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}}
li{{margin:.2rem 0}}code{{background:#f2f2f2;padding:.1rem .3rem;border-radius:4px}}</style></head>
<body><h1>MLBB Historical Database — Static API</h1>
<p>Static JSON mirror of all <b>{len(built)}</b> endpoints. Serve this folder via GitHub Pages,
or run the live FastAPI server (see <a href="https://github.com/ryujin-hue/mlbb-historical-database#readme">README</a>).
Values shown are representative examples for endpoints with path parameters.</p>
<ul>
{rows}
</ul></body></html>
"""
(STATIC.parent / "index.html").write_text(html, encoding="utf-8")
print("api/static/index.html written")

# ---------------- API.md ----------------
by_tag: dict[str, list[tuple[str, str, str]]] = {}
for template in GET_PATHS:
    by_tag.setdefault(GET_TAG[template], []).append((template, GET_SUMMARY[template], ""))

order = ["meta", "heroes", "extras", "items", "patches", "mseries",
         "esports", "systems", "client", "business", "reference"]
lines = []
total = 0
for tag in order:
    eps = sorted(by_tag.get(tag, []))
    total += len(eps)
    lines.append(f"\n### `{tag}` — {len(eps)} endpoints\n")
    lines.append("| # | Method | Endpoint | Description | Static mirror |")
    lines.append("|---|--------|----------|-------------|---------------|")
    for i, (p, s, _) in enumerate(eps, 1):
        fname = static_name(example_path(p))
        lines.append(f"| {total - len(eps) + i} | GET | `{p}` | {s} | [`v1/{fname}`](api/static/v1/{fname}) |")
assert total == 78, f"API.md table mismatch: {total}"
endpoint_table = "\n".join(lines)

api_md = f"""# MLBB Historical Database — REST API

Open, read-only REST API over the MLBB historical database (2016 → Oct 2026).
**Exactly 78 GET endpoints** (verified by `tests/test_api.py::test_exactly_78_endpoints`).
All data is served from the repository's own CSV files — no external calls at request time.

- Datasets: 12 tables (989+ rows) — patches, hero/item balance history, M-Series, esports, systems, client/collabs, business
- Reference tables: 13 lookups in [`references/`](references/) — roles, lanes, spells, emblems, ranked ladder, game modes, ...
- Images: 683 sourced images also served at `/img/<path>` by the live server

## Quickstart

```bash
pip install -r api/requirements.txt
uvicorn api.main:app --reload
# Interactive docs: http://127.0.0.1:8000/docs
```

## Two ways to consume

1. **Live server** (FastAPI): run the command above, or deploy it anywhere Python runs.
2. **Static JSON mirror** (no server needed): [`api/static/v1/`](api/static/v1/) contains one JSON file per
   endpoint (78 files), generated by `scripts/build_api_artifacts.py`. Serve the `api/static/` folder on
   GitHub Pages: *Settings → Pages → deploy from branch → select `/api/static` root* (or host anywhere static).
   Path-parameter endpoints are mirrored with representative example values.

Response envelope for list endpoints:

```json
{{"endpoint": "/api/v1/heroes", "count": 50, "total": 133, "limit": 50, "offset": 0, "data": [ ... ]}}
```

Common query parameters: `limit` (default 50, max 1000), `offset`, plus per-endpoint filters
(`role`, `lane`, `year`, `change_type`, `version`, `category`, `aspect`, `topic`, `q` for search).

## OpenAPI

Machine-readable spec: [`api/openapi.json`](api/openapi.json) — import into Postman/Insomnia or
generate client SDKs (`openapi-generator`).

## Endpoint catalog — all 78

| Tag | Endpoints |
|-----|-----------|
{chr(10).join(f"| `{t}` | {len(by_tag.get(t, []))} |" for t in order)}
| **Total** | **78** |
{endpoint_table}

## Notes on the data

- `UNVERIFIED` values inside records are preserved verbatim — facts that could not be double-sourced
  are flagged, never fabricated (see [`research_report.md`](research_report.md) §5).
- Patch dates for 2016–2019 are partially year-only (exact dates UNVERIFIED) — the `patches/year/2024`
  endpoint legitimately returns an empty result because no 2024-dated rows exist in `patch_index.csv`.
- M-Series prize pools and viewership are USD / peak-concurrent viewers as recorded at research time (Oct 2026).
- Esports table currently covers MPL Philippines S1–S18 plus international events (MSC, EWC-era MSC, MWI);
  other MPL regions remain a documented PARTIAL-coverage gap (research_report.md §5).
"""
(REPO / "API.md").write_text(api_md, encoding="utf-8")
print("API.md written")

# ---------------- references/README.md ----------------
ref_md = """# Reference Data (lookup tables)

Derived lookup tables feeding `/api/v1/reference/*` and `/api/v1/systems/*` endpoints.
Every row is derived from the repo's verified datasets — no fabricated values; unknown
attributes stay empty. Regenerate with `python3 scripts/build_reference_data.py`.

| Table | Rows | Contents |
|-------|------|----------|
| hero_roles.csv | 24 | Hero roles (incl. multi-role tags like fighter/assassin) + counts |
| hero_lanes.csv | 14 | Lane assignments (Gold/EXP/Mid/Jungle/Roam + combos) + counts |
| lore_regions.csv | 14 | In-game lore regions from official mlbb.io hero pages |
| item_categories.csv | 16 | Item shop categories with counts and price ranges |
| battle_spells.csv | 12 | Current 12 battle spells with cooldowns and effects |
| emblem_sets.csv | 7 | Post-1.7.44 emblem sets; base attributes where documented |
| ranked_ladder.csv | 10 | Warrior → Mythical Immortal ladder with star bands |
| game_modes.csv | 17 | All game modes with launch periods and status |
| change_types.csv | 21 | Change-type taxonomy (raw + normalized) with record counts |
| host_countries.csv | 7 | M-Series/esports host countries with event counts |
| currencies.csv | 13 | ISO 4217 currencies for host/esports markets (prize pools are USD) |
| tournament_event_types.csv | 5 | Event-type taxonomy (M-Series, MSC/EWC, MWI, MPL) |
| data_dictionary.csv | 24 | Column-level data dictionary for every table in the repo |
"""
(REPO / "references" / "README.md").write_text(ref_md, encoding="utf-8")
print("references/README.md written")
print("\nAll API artifacts built successfully.")
