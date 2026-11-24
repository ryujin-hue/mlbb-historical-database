<div align="center">

<img src="assets/logo-mlbb-a.svg" alt="MLBB Almanac" width="380" />

# MLBB Almanac — Archive (2016 → 2026)

**Ten years of patch history for Mobile Legends: Bang Bang.**

[![Datasets](https://img.shields.io/badge/datasets-12%20tables-2ea44f)](.)
[![API](https://img.shields.io/badge/API-78%20endpoints-blue)](API.md)
[![Images](https://img.shields.io/badge/images-683%20sourced-orange)](images_manifest.csv)

</div>

---

> **This repository is now `archive/` inside the
> [mlbb-almanac](https://github.com/ryujin-hue/mlbb-almanac) monorepo.**
> That repository is the source of truth: it carries this tree under
> `archive/`, compiles these datasets into the live site, and runs the daily
> updater from there.
>
> This repository stays readable and its own auto-update keeps running, so
> the archive keeps growing either way.
>
> **The data now lives in the site:** <https://mlbb-almanac.pages.dev>

## What it holds

| | |
|---|---|
| **87** | patch versions, `1.1.23.109.1` (2016) → `2.2.23` (2026-11-11) |
| **350** | hero balance changes — buff, nerf, adjust, rework, release |
| **99** | item changes across the shop |
| **133** | heroes: role, lane, release version, release date, price, buff/nerf counts |
| **104** | shop items: category, gold cost, build path, unique passive |
| **13** | reference lookup tables |
| **78** | REST API endpoints |
| **683** | source-credited images |
| **5** | research documents (glossary, timeline, meta history, academy summary, research report) |

## Layout

| Path | Contents |
|---|---|
| `*.csv` | Core datasets: `patch_index`, `hero_changes`, `hero_master`, `item_changes`, `items_master`, `mseries`, `esports`, `systems`, `client`, `business`, `heroes_extra`, `images_manifest` |
| `references/` | 13 lookup tables — roles, lanes, lore regions, battle spells with cooldowns, emblem sets, ranked ladder, game modes, change-type taxonomy, host countries, currencies, event types, item categories, data dictionary |
| `api/` | FastAPI application, exactly 78 GET endpoints, `openapi.json`, and a static JSON mirror (`api/static/v1/`, one file per endpoint) |
| `images/` | 683 source-credited images (734 files on disk) |
| `*.md` | `research_report.md` (57-scope audit: 38 covered / 17 partial / 1 gap), `meta_history.md` (8 meta eras), `timeline.md` (2016→2026 chronology), `glossary.md` (EN/ID/MS), `academy_summary.md` |
| `scripts/` | `update_data.py` (daily updater), `build_reference_data.py`, `build_api_artifacts.py` |
| `tests/` | pytest suite — enforces the 78-endpoint contract and exercises every endpoint |
| `updates/` | `last_update.json`, `season_status.json`, `UPDATELOG.md` |

## API — 78 endpoints

Full catalog: [`API.md`](API.md) · machine spec: [`api/openapi.json`](api/openapi.json)

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

No server? Use the static mirror: `api/static/v1/` holds one JSON file per
endpoint. The count is enforced by `tests/test_api.py::test_exactly_78_endpoints`.

```bash
curl localhost:8000/api/v1/heroes/lancelot              # hero detail
curl localhost:8000/api/v1/heroes/changes/patch/2.2.16  # exact old → new values
curl localhost:8000/api/v1/mseries/m7                   # 5,680,511 peak viewers
curl localhost:8000/api/v1/patches/latest               # latest patch + date
curl localhost:8000/api/v1/systems/battle-spells        # 12 spells with cooldowns
```

## It updates itself

1. **Scheduled** — `.github/workflows/auto-update.yml` runs daily at 02:00
   Asia/Kuala_Lumpur (cron `0 18 * * *` UTC), or on demand via *workflow_dispatch*.
2. **Detect** — `scripts/update_data.py` diffs live snapshots from mlbbhub.com
   against the datasets: a new patch version, a new hero, a new shop item or
   battle spell, a ranked season rollover.
3. **Apply** — appended rows are tagged `(auto-update)` with their source URL
   and `UNVERIFIED` flags where a human pass is still owed. Derived reference
   tables and the static API mirror are regenerated in the same run.
4. **Commit** — the workflow commits `[auto-update] data refresh <date>`;
   `updates/UPDATELOG.md` records every run.

Locally: `python3 scripts/update_data.py` (add `--dry-run` to preview).

## Method

- Every record carries its own source URL; key facts were cross-verified
  against two or more independent sources.
- Values that could not be double-sourced are flagged `UNVERIFIED` **in-band**
  — never silently invented.
- Conflicting sources are kept and documented (`research_report.md` §5).
- Known gap: per-level hero base-stat growth tables need game-file mining;
  the esports table covers MPL Philippines and international events, other MPL
  regions remain a documented partial gap.
- Data cutoff: **2026-11-11** (patch `2.2.23`).

## Regenerate

```bash
python3 scripts/build_reference_data.py   # rebuild references/*.csv
python3 scripts/build_api_artifacts.py    # rebuild static mirror + openapi.json + API.md
python3 -m pytest tests/ -q               # archive test suite
```

## In the site

These datasets are not just an archive — they are the history half of
[MLBB Almanac](https://mlbb-almanac.pages.dev). The monorepo compiles them
into static JSON during the web build, so every patch note, item change and
reference table is browsable next to live win rates.
