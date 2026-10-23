"""Heroes router — 14 endpoints (master roster + balance-change history)."""
import random

from fastapi import APIRouter, HTTPException, Query

from ..data import (envelope, first_year, load, paginate, slugify, with_image_url)

router = APIRouter(tags=["heroes"])

HEROES = lambda: load("hero_master.csv")  # noqa: E731
CHANGES = lambda: with_image_url(load("hero_changes.csv"))  # noqa: E731


def _find(hero: str) -> dict:
    target = slugify(hero)
    for h in HEROES():
        if slugify(h["hero"]) == target:
            return h
    raise HTTPException(404, detail=f"hero not found: {hero}")


@router.get("/api/v1/heroes", summary="List all heroes")
def heroes(role: str | None = None, lane: str | None = None,
           limit: int = Query(50, le=1000), offset: int = 0):
    rows = HEROES()
    if role:
        rows = [h for h in rows if role.lower() in h["role"].lower()]
    if lane:
        rows = [h for h in rows if lane.lower() in h["lane"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/heroes", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/heroes/count", summary="Hero count")
def heroes_count():
    roles = sorted({h["role"].split("/")[0] for h in HEROES()})
    return envelope("/api/v1/heroes/count", {"total": len(HEROES()),
                                             "primary_roles": roles})


@router.get("/api/v1/heroes/random", summary="Random hero(es)")
def heroes_random(n: int = Query(1, le=20)):
    return envelope("/api/v1/heroes/random", random.sample(HEROES(), min(n, len(HEROES()))))


@router.get("/api/v1/heroes/search", summary="Search heroes by name")
def heroes_search(q: str, limit: int = Query(20, le=100)):
    q = q.lower()
    hits = [h for h in HEROES() if q in h["hero"].lower()]
    return envelope("/api/v1/heroes/search", hits[:limit], total=len(hits))


@router.get("/api/v1/heroes/latest", summary="Most recently released heroes")
def heroes_latest(n: int = Query(5, le=50)):
    rows = sorted(HEROES(), key=lambda h: h["release_date"], reverse=True)
    return envelope("/api/v1/heroes/latest", rows[:n])


@router.get("/api/v1/heroes/role/{role}", summary="Heroes by role")
def heroes_role(role: str):
    rows = [h for h in HEROES() if role.lower() in h["role"].lower()]
    if not rows:
        raise HTTPException(404, detail=f"no heroes with role {role}")
    return envelope(f"/api/v1/heroes/role/{role}", rows, total=len(rows))


@router.get("/api/v1/heroes/lane/{lane}", summary="Heroes by lane")
def heroes_lane(lane: str):
    rows = [h for h in HEROES() if lane.lower() in h["lane"].lower()]
    if not rows:
        raise HTTPException(404, detail=f"no heroes for lane {lane}")
    return envelope(f"/api/v1/heroes/lane/{lane}", rows, total=len(rows))


@router.get("/api/v1/heroes/year/{year}", summary="Heroes released in a year")
def heroes_year(year: str):
    rows = [h for h in HEROES() if first_year(h["release_date"]) == year]
    if not rows:
        raise HTTPException(404, detail=f"no heroes released in {year}")
    return envelope(f"/api/v1/heroes/year/{year}", rows, total=len(rows))


@router.get("/api/v1/heroes/lore-region/{region}", summary="Heroes by lore region")
def heroes_lore_region(region: str):
    region_lower = region.lower()
    rows = []
    for r in load("lore_regions.csv", ref=True):
        if region_lower in r["region"].lower():
            names = [x.strip() for x in r["heroes"].split(",") if x.strip()]
            for name in names:
                rows.extend(h for h in HEROES() if slugify(h["hero"]) == slugify(name))
    if not rows:
        raise HTTPException(404, detail=f"no lore region matching {region}")
    return envelope(f"/api/v1/heroes/lore-region/{region}", rows,
                    region=[r["region"] for r in load("lore_regions.csv", ref=True)
                            if region_lower in r["region"].lower()])


@router.get("/api/v1/heroes/changes", summary="All hero balance changes")
def heroes_changes(change_type: str | None = None, version: str | None = None,
                   year: str | None = None, hero: str | None = None,
                   limit: int = Query(50, le=1000), offset: int = 0):
    rows = CHANGES()
    if change_type:
        rows = [r for r in rows if r["change_type"].lower() == change_type.lower()]
    if version:
        rows = [r for r in rows if r["version"].lower() == version.lower()]
    if year:
        rows = [r for r in rows if first_year(r["date"]) == year]
    if hero:
        rows = [r for r in rows if slugify(hero) in slugify(r["hero"])]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/heroes/changes", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/heroes/changes/type/{change_type}", summary="Hero changes by type")
def heroes_changes_type(change_type: str, limit: int = Query(50, le=1000), offset: int = 0):
    rows = [r for r in CHANGES() if r["change_type"].lower() == change_type.lower()]
    if not rows:
        raise HTTPException(404, detail=f"no changes of type {change_type}")
    page, total = paginate(rows, limit, offset)
    return envelope(f"/api/v1/heroes/changes/type/{change_type}", page,
                    total=total, limit=limit, offset=offset)


@router.get("/api/v1/heroes/changes/patch/{version}", summary="Hero changes in a patch")
def heroes_changes_patch(version: str):
    rows = [r for r in CHANGES() if r["version"].lower() == version.lower()]
    if not rows:
        raise HTTPException(404, detail=f"no hero changes recorded for patch {version}")
    return envelope(f"/api/v1/heroes/changes/patch/{version}", rows, total=len(rows))


@router.get("/api/v1/heroes/{hero}", summary="Hero detail")
def hero_detail(hero: str):
    return envelope(f"/api/v1/heroes/{hero}", _find(hero))


@router.get("/api/v1/heroes/{hero}/changes", summary="Balance history of one hero")
def hero_changes(hero: str, limit: int = Query(50, le=1000), offset: int = 0):
    h = _find(hero)
    rows = [c for c in CHANGES() if slugify(c["hero"]) == slugify(h["hero"])]
    page, total = paginate(rows, limit, offset)
    return envelope(f"/api/v1/heroes/{hero}/changes", page, total=total,
                    limit=limit, offset=offset,
                    hero_summary={k: h[k] for k in
                                  ("hero", "role", "lane", "release_date", "release_version",
                                   "total_buffs", "total_nerfs", "total_adjusts")})
