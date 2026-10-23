# MLBB Historical Database (2016 → 2026)

A fully-sourced, cross-verified historical database of **Mobile Legends: Bang Bang** —
patches, hero and item balance history, game systems, the M-Series world championship,
esports events, client/platform history and Moonton business records — with **exactly 78
REST API endpoints** and **13 reference lookup tables**.

![data](https://img.shields.io/badge/datasets-12%20tables-2ea44f) ![api](https://img.shields.io/badge/API-78%20endpoints-blue) ![images](https://img.shields.io/badge/images-683%20sourced-orange)

## What's inside

| Path | Contents |
|------|----------|
| `*.csv` (12 tables) | Core datasets: `patch_index` (86 versions 1.1.23.109.1 → 2.2.16a, incl. auto-detected hotfixes), `hero_changes` (350+ rows with old→new values), `hero_master` (133 heroes), `item_changes` (99), `items_master` (104-item shop snapshot), `mseries` (M1–M7 + announced M8), `esports` (38 events), `systems` (98), `client` (53, incl. 18 collabs), `business` (70), `heroes_extra` (45), `images_manifest` (683) |
| `references/` | **13 reference/lookup tables** (roles, lanes, lore regions, battle spells with cooldowns, emblem sets, ranked ladder, game modes, change-type taxonomy, host countries, currencies, event types, item categories, data dictionary) |
| `api/` | **FastAPI application with exactly 78 GET endpoints** + `openapi.json` + static JSON mirror (`api/static/v1/`, one file per endpoint) |
| `images/` | 683 locally-stored, source-credited images (heroes, items, emblems, spells, events, teams) |
| `reports/` (5 `.md`) | `research_report.md` (57-scope-item audit: 38 COVERED / 17 PARTIAL / 1 GAP), `meta_history.md` (8 meta eras), `timeline.md` (2016→2026 chronology), `glossary.md` (EN/ID/MS), `academy_summary.md` |
| `tests/` | pytest suite — asserts the **exactly-78-endpoint** contract and exercises every endpoint |
| `scripts/` | `update_data.py` (automatic live updater), `build_reference_data.py`, `build_api_artifacts.py` — regenerate all derived data/docs |
| `updates/` | `last_update.json` (machine-readable status), `season_status.json`, `UPDATELOG.md` (run history) |
| `.github/workflows/auto-update.yml` | **Daily scheduled auto-update** (02:00 Asia/Kuala_Lumpur) |

## API (78 endpoints, verified)

Full catalog: **[API.md](API.md)** · Machine spec: [`api/openapi.json`](api/openapi.json) · Interactive docs at `/docs` when running.

```bash
pip install -r api/requirements.txt
uvicorn api.main:app --reload        # http://127.0.0.1:8000/docs
```

| Tag | Endpoints | Tag | Endpoints |
|-----|-----------|-----|-----------|
| `meta` | 6 | `mseries` | 7 |
| `heroes` | 14 | `esports` | 7 |
| `extras` | 2 | `systems` | 7 |
| `items` | 8 | `client` | 4 |
| `patches` | 8 | `business` | 4 |
| — | — | `reference` | 11 |
| | | **Total** | **78** |

No server? Use the **static JSON mirror**: `api/static/v1/` holds one JSON file per endpoint
(path-parameter endpoints use representative examples) — host it on GitHub Pages or read the
files directly. Endpoint counts are enforced by `tests/test_api.py::test_exactly_78_endpoints`.

Example queries:

```bash
curl localhost:8000/api/v1/heroes/lancelot            # hero detail
curl localhost:8000/api/v1/heroes/changes/patch/2.2.16  # exact old->new values
curl localhost:8000/api/v1/mseries/m7                 # 5,680,511 peak viewers record
curl localhost:8000/api/v1/patches/latest             # 2.2.16a (2026-10-14)
curl localhost:8000/api/v1/systems/battle-spells      # 12 spells w/ cooldowns
```

## Automatic updates (data grows by itself)

The repo **updates itself when a live update lands**:

1. **Scheduled run** — `.github/workflows/auto-update.yml` runs daily at 02:00 Asia/Kuala_Lumpur
   (cron `0 18 * * *` UTC), or trigger it manually from the GitHub Actions tab (*workflow_dispatch*).
2. **Detection** — `scripts/update_data.py` fetches live snapshots from mlbbhub.com and diffs
   them against the repo's datasets:
   - new **patch version** (e.g. 2.2.17) → appended to `patch_index.csv`
   - new **hero** (roster grows past 133) → appended to `hero_master.csv` + `hero_changes.csv`,
     splash art downloaded to `images/heroes/`
   - new **shop item** or **battle spell** → appended to `item_changes.csv` / `systems.csv`
   - ranked **season rollover** → recorded in `updates/season_status.json`
3. **Apply** — appended rows are tagged `(auto-update)` with source URL and `UNVERIFIED` flags
   where a human research pass is still needed (exact dates, old→new values). Derived reference
   tables and the 78-file static API mirror are regenerated in the same run.
4. **Commit** — if anything changed, the workflow commits `[auto-update] data refresh <date>`
   and pushes; `updates/UPDATELOG.md` records every run (see `updates/last_update.json` for
   machine-readable status).

Run it locally anytime: `python3 scripts/update_data.py` (add `--dry-run` to preview).

## Method & honesty rules

- Every record carries its `source` URL(s); key facts were cross-verified with 2+ independent sources.
- Values that could not be double-sourced are flagged `UNVERIFIED` **in-band** — never silently invented.
- Conflicting sources are kept and documented (see `research_report.md` §5 CONFLICTS register).
- Known GAP: per-level hero base-stat growth tables (requires game-file mining); esports table covers
  MPL Philippines + international events — other MPL regions remain a documented PARTIAL gap.
- Data cutoff: **2026-10-22** (live patch 2.2.16 / hotfix 2.2.16a, Season 42).

## Reproduce / regenerate

```bash
python3 scripts/build_reference_data.py   # rebuilds references/*.csv from verified research data
python3 scripts/build_api_artifacts.py    # rebuilds static mirror + openapi.json + API.md
python3 -m pytest tests/ -q               # 13 tests incl. the 78-endpoint contract
```
