#!/usr/bin/env python3
"""Automatic data updater for the MLBB Historical Database.

Detects live changes on mlbbhub.com (reachable public mirror of official data)
and appends only genuinely NEW records to the repo's CSV datasets:

  - new patch versions      -> patch_index.csv
  - new heroes              -> hero_master.csv + hero_changes.csv (+ splash art download)
  - new shop items          -> item_changes.csv
  - new battle spells       -> systems.csv
  - ranked season rollover  -> updates/season_status.json (log only)

Then refreshes the derived reference tables (roles/lanes/categories/change
types/data dictionary), rebuilds the static API mirror + API.md, and writes
updates/last_update.json + updates/UPDATELOG.md.

Designed to run in GitHub Actions on a schedule (see .github/workflows/
auto-update.yml) or locally:  python3 scripts/update_data.py [--dry-run]

Honesty rules: appended rows are tagged "(auto-update)" and carry their source
URL; values that need a human research pass (exact dates, numbers) are flagged
UNVERIFIED — never invented.
"""
import csv
import io
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPDATES = REPO / "updates"
TZ8 = timezone(timedelta(hours=8))  # Asia/Kuala_Lumpur
RUN_TAG = datetime.now(TZ8).strftime("%Y-%m-%d %H:%M (+08)")
TODAY = datetime.now(TZ8).strftime("%Y-%m-%d")
UA = {"User-Agent": "mlbb-historical-database-updater/1.0 (data repo; contact via GitHub issues)"}

SOURCES = {
    "heroes": "https://mlbbhub.com/heroes",
    "patches": "https://mlbbhub.com/patch-notes",
    "items": "https://mlbbhub.com/items",
    "spells": "https://mlbbhub.com/spells",
    "season": "https://mlbbhub.com/server-time/season-schedule",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower()).strip("-")


# ----------------------------------------------------------------- parsers
def parse_heroes(html: str) -> list[dict]:
    """Extract the embedded escaped-JSON heroes array from the RSC payload."""
    anchor = html.find('\\"heroes\\":[')
    if anchor < 0:
        raise RuntimeError("heroes payload anchor not found on live page")
    start = html.find("[", anchor)
    seg = html[start:start + 400_000].replace('\\"', '"')
    heroes, _ = json.JSONDecoder().raw_decode(seg)
    return heroes


def latest_patch(html: str) -> tuple[str, str]:
    """(version, date) of the latest patch block; date '' if not found."""
    i = html.find('\\"version\\":\\"')
    if i < 0:
        raise RuntimeError("patch version key not found on live page")
    seg = html[i:i + 1500].replace('\\"', '"')
    m = re.search(r'"version":"([0-9]+\.[0-9]+\.[0-9]+[a-z]?)"', seg)
    version = m.group(1) if m else "UNKNOWN"
    d = re.search(r"(January|February|March|April|May|June|July|August|September|"
                  r"October|November|December) (\d{1,2}), (20\d\d)", seg)
    date = f"{d.group(3)}-{dict((m, i+1) for i, m in enumerate(
        ['january','february','march','april','may','june','july','august',
         'september','october','november','december']))[d.group(1).lower()]:02d}-{int(d.group(2)):02d}" if d else ""
    return version, date


def item_slugs(html: str) -> set[str]:
    return set(re.findall(r'\\"slug\\":\\"([a-z0-9-]+)\\"', html))


def season_status(html: str) -> dict:
    """Best-effort current-season number and end date."""
    out: dict = {"season": None, "end_date": None}
    m = re.search(r"Season (\d+)", html)
    if m:
        out["season"] = int(m.group(1))
    d = re.search(r"(January|February|March|April|May|June|July|August|September|"
                  r"October|November|December) (\d{1,2}), (20\d\d)", html)
    if d:
        out["end_date"] = f"{d.group(3)}-{d.group(1)[:3].upper()}-{int(d.group(2)):02d}"
    return out


# ----------------------------------------------------------------- csv io
def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writerows(rows)


# ----------------------------------------------------------------- merges
def new_heroes(live: list[dict], master: list[dict]) -> list[dict]:
    known = {slugify(h["hero"]) for h in master}
    return [h for h in live if slugify(h["name"]) not in known]


def hero_master_row(h: dict, img_rel: str | None) -> dict:
    return {
        "hero": h["name"],
        "role": "/".join(h.get("role") or []).lower(),
        "lane": "/".join(h.get("lane") or []),
        "release_version": "UNVERIFIED (auto-update; verify vs official patch notes)",
        "release_date": f"{h.get('releaseYear')} (year-only, day UNVERIFIED; auto-update {TODAY})",
        "price_bp": "", "price_diamond": "", "reworked_or_revamped": "",
        "total_buffs": 0, "total_nerfs": 0, "total_adjusts": 0,
        "sources": f"{SOURCES['heroes']} (auto-update {TODAY}); https://mlbbhub.com/hero/{h['slug']}",
        "image_path": img_rel or "MISSING_IMAGE",
        "image_source": (h.get("splashArt") or "") if img_rel else "MISSING_IMAGE",
    }


def hero_change_row(h: dict, img_rel: str | None) -> dict:
    return {
        "version": "",
        "date": f"{h.get('releaseYear')} (year-only, UNVERIFIED; auto-update {TODAY})",
        "hero": h["name"],
        "change_type": "New",
        "detail": ("Released — auto-detected via mlbbhub live roster snapshot "
                   f"(auto-update {RUN_TAG}); exact release version/values pending "
                   "manual verification against official patch notes"),
        "source": f"https://mlbbhub.com/hero/{h['slug']} (auto-update {TODAY})",
        "image_path": img_rel or "MISSING_IMAGE",
        "image_source": (h.get("splashArt") or "") if img_rel else "MISSING_IMAGE",
    }


def download_splash(slug: str, url: str) -> str | None:
    if not url or not url.startswith("http"):
        return None
    ext = ".jpg" if ".jpg" in url or ".jpeg" in url else ".png"
    dest = REPO / "images" / "heroes" / f"{slug}{ext}"
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=30).read()
        dest.write_bytes(data)
        return f"images/heroes/{dest.name}"
    except Exception:
        return None


# ------------------------------------------------- derived reference refresh
def refresh_derived_tables() -> None:
    """Recompute roles/lanes/categories/change-types/data-dictionary counts."""
    ref = REPO / "references"
    heroes = read_csv(REPO / "hero_master.csv")

    roles: dict[str, int] = {}
    for h in heroes:
        r = (h["role"] or "").strip().lower()
        if r:
            roles[r] = roles.get(r, 0) + 1
    write_lookup(ref / "hero_roles.csv",
                 ["role", "hero_count", "description"],
                 [{"role": r, "hero_count": n, "description": ""}
                  for r, n in sorted(roles.items(), key=lambda x: -x[1])])

    lanes: dict[str, int] = {}
    for h in heroes:
        l = (h["lane"] or "").strip()
        if l:
            lanes[l] = lanes.get(l, 0) + 1
    write_lookup(ref / "hero_lanes.csv",
                 ["lane", "hero_count", "description"],
                 [{"lane": l, "hero_count": n, "description": ""}
                  for l, n in sorted(lanes.items(), key=lambda x: -x[1])])

    items = read_csv(REPO / "items_master.csv")
    cats: dict[str, dict] = {}
    for it in items:
        c = it["category"].strip()
        d = cats.setdefault(c, {"n": 0, "min": 10**9, "max": 0, "items": []})
        d["n"] += 1
        d["items"].append(it["item"])
        if it["price_gold"].strip().isdigit():
            p = int(it["price_gold"])
            d["min"], d["max"] = min(d["min"], p), max(d["max"], p)
    write_lookup(ref / "item_categories.csv",
                 ["category", "item_count", "min_price_gold", "max_price_gold", "items"],
                 [{"category": c, "item_count": d["n"],
                   "min_price_gold": d["min"] if d["min"] < 10**9 else "",
                   "max_price_gold": d["max"] or "", "items": ", ".join(d["items"])}
                  for c, d in sorted(cats.items())])

    NORM = {"New": "New", "added": "New", "Buff": "Buff", "buff": "Buff",
            "Nerf": "Nerf", "nerf": "Nerf", "Adjust": "Adjust", "changed": "Adjust",
            "Rework": "Rework", "rework": "Rework", "Remove": "Removed",
            "removed": "Removed", "Rename": "Rename", "Replace": "Replaced",
            "repriced": "Repriced", "bugfix": "Bugfix"}
    rows = []
    for src_file in ("hero_changes.csv", "item_changes.csv"):
        counts: dict[str, int] = {}
        for r in read_csv(REPO / src_file):
            raw = r["change_type"].strip()
            counts[raw] = counts.get(raw, 0) + 1
        for raw, n in counts.items():
            rows.append({"dataset": src_file.replace(".csv", ""), "raw_change_type": raw,
                         "normalized_type": NORM.get(raw, raw), "record_count": n})
    rows.sort(key=lambda x: (x["dataset"], -x["record_count"]))
    write_lookup(ref / "change_types.csv",
                 ["dataset", "raw_change_type", "normalized_type", "record_count"], rows)

    # data dictionary row counts
    dd_path = ref / "data_dictionary.csv"
    dd = read_csv(dd_path)
    for r in dd:
        f = REPO / r["file"]
        if f.exists():
            r["row_count"] = len(read_csv(f))
    write_lookup(dd_path, list(dd[0].keys()), dd)

    # keep items_master item slugs in sync with live-shop detection: categories refresh only


def write_lookup(path: Path, header: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


# ----------------------------------------------------------------- logging
def write_logs(applied: bool, detected: dict, season: dict, rebuilt: bool) -> None:
    UPDATES.mkdir(exist_ok=True)
    payload = {
        "run_at": RUN_TAG,
        "applied": applied,
        "sources_checked": SOURCES,
        "detected_new": detected,
        "season_status": season,
        "static_api_rebuilt": rebuilt,
        "rows_appended": sum(len(v) for v in detected.values()),
    }
    (UPDATES / "last_update.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    log = UPDATES / "UPDATELOG.md"
    if not log.exists():
        log.write_text("# Auto-Update Log\n\nGenerated by `scripts/update_data.py` "
                       "(runs daily via GitHub Actions; +08 timezone).\n\n"
                       "| Run | Detected | Applied | Detail |\n|---|---|---|---|\n",
                       encoding="utf-8")
    if any(detected.values()):
        parts = [f"{k}: {', '.join(v)}" for k, v in detected.items() if v]
        detail = "; ".join(parts)
    else:
        detail = f"no changes (latest patch {(season.get('latest_patch') or 'n/a')}, " \
                 f"season {season.get('season') or 'n/a'}; roster/items/spells unchanged)"
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"| {RUN_TAG} | {'yes' if detected else 'no'} | "
                f"{'yes' if applied else 'no (dry-run)' if detected else 'n/a'} | {detail} |\n")


def rebuild_static_api() -> bool:
    try:
        import fastapi  # noqa: F401
        r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_api_artifacts.py")],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(r.stdout[-800:], r.stderr[-800:])
            return False
        return True
    except ImportError:
        print("fastapi not installed — skipping static API rebuild")
        return False


# ----------------------------------------------------------------- main
def main(dry_run: bool = False) -> int:
    detected: dict[str, list[str]] = {"patches": [], "heroes": [], "items": [], "spells": []}
    master = read_csv(REPO / "hero_master.csv")
    patches = read_csv(REPO / "patch_index.csv")
    items = read_csv(REPO / "items_master.csv")
    spells = read_csv(REPO / "references" / "battle_spells.csv")

    # ---- patches
    phtml = fetch(SOURCES["patches"])
    version, date = latest_patch(phtml)
    known_versions = {p["version"].lower() for p in patches}
    new_patch_row = None
    if version.lower() not in known_versions and version != "UNKNOWN":
        detected["patches"].append(version)
        new_patch_row = {"version": version,
                         "date": date or f"date UNVERIFIED (auto-update {TODAY})",
                         "source": f"{SOURCES['patches']} (auto-update {TODAY})"}

    # ---- heroes
    heroes_live = parse_heroes(fetch(SOURCES["heroes"]))
    added_heroes = new_heroes(heroes_live, master)

    # ---- items
    live_items = item_slugs(fetch(SOURCES["items"]))
    known_items = {slugify(i["item"]) for i in items}
    added_items = sorted(s for s in live_items if slugify(s) not in known_items)

    # ---- spells
    try:
        live_spells = item_slugs(fetch(SOURCES["spells"]))
        known_spells = {slugify(s["spell"]) for s in spells}
        added_spells = sorted(s for s in live_spells if slugify(s) not in known_spells)
    except Exception:
        added_spells = []

    if added_heroes:
        detected["heroes"] = [h["name"] for h in added_heroes]
    if added_items:
        detected["items"] = added_items
    if added_spells:
        detected["spells"] = added_spells

    # ---- season snapshot
    season = season_status(fetch(SOURCES["season"]))
    season["latest_patch"] = version + (f" ({date})" if date else "")
    prev = UPDATES / "season_status.json"
    season_changed = True
    if prev.exists():
        try:
            old = json.loads(prev.read_text(encoding="utf-8"))
            season_changed = (old.get("season") != season["season"] or
                              old.get("end_date") != season["end_date"])
        except Exception:
            pass

    print(f"[{RUN_TAG}] live check: patch={version} ({date or 'date n/a'}), "
          f"heroes={len(heroes_live)} (new: {len(added_heroes)}), "
          f"items={len(live_items)} (new: {len(added_items)}), "
          f"spells new: {len(added_spells)}, season={season['season']}")

    if not (detected["patches"] or detected["heroes"] or detected["items"] or
            detected["spells"] or season_changed):
        write_logs(applied=False, detected=detected, season=season, rebuilt=False)
        print("no live updates to apply")
        return 0

    if dry_run:
        write_logs(applied=False, detected=detected, season=season, rebuilt=False)
        print(f"DRY-RUN — would append: {detected}")
        return 0

    # ---- apply
    if new_patch_row:
        append_csv(REPO / "patch_index.csv", [new_patch_row])
    for h in added_heroes:
        img = download_splash(h["slug"], h.get("splashArt") or "")
        append_csv(REPO / "hero_master.csv", [hero_master_row(h, img)])
        append_csv(REPO / "hero_changes.csv", [hero_change_row(h, img)])
    if added_items:
        rows = [{"version": "", "date": f"detected {TODAY} (exact date UNVERIFIED; auto-update)",
                 "item": s.replace("-", " ").title(),
                 "change_type": "added",
                 "detail": ("New item detected in live mlbbhub shop snapshot "
                            f"(auto-update {RUN_TAG}); price/category/passives pending "
                            "manual verification"),
                 "source": f"https://mlbbhub.com/items/{s} (auto-update {TODAY})",
                 "image_path": "MISSING_IMAGE", "image_source": "MISSING_IMAGE"}
                for s in added_items]
        append_csv(REPO / "item_changes.csv", rows)
    if added_spells:
        rows = [{"system": "Spell", "aspect": "New battle spell (auto-update)",
                 "period_or_version": f"UNVERIFIED (auto-update {TODAY})",
                 "detail": (f"Spell slug '{s}' detected on mlbbhub live spell list but not "
                            f"in the verified 12-spell baseline; effects pending manual "
                            "verification against official patch notes"),
                 "source": f"https://mlbbhub.com/spells (auto-update {TODAY})",
                 "image_path": "MISSING_IMAGE", "image_source": "MISSING_IMAGE"}
                for s in added_spells]
        append_csv(REPO / "systems.csv", rows)

    (UPDATES).mkdir(exist_ok=True)
    (UPDATES / "season_status.json").write_text(
        json.dumps(season, indent=2), encoding="utf-8")

    refresh_derived_tables()
    rebuilt = rebuild_static_api()
    write_logs(applied=True, detected=detected, season=season, rebuilt=rebuilt)
    print(f"applied: {detected} | static api rebuilt: {rebuilt}")
    return 0


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
