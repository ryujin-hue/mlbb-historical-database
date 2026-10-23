"""Systems router — 7 endpoints (game systems + system reference tables)."""
from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, load, paginate

router = APIRouter(tags=["systems"])

SYS = lambda: load("systems.csv")  # noqa: E731


@router.get("/api/v1/systems", summary="List game-system records")
def systems(system: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = SYS()
    if system:
        rows = [r for r in rows if system.lower() == r["system"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/systems", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/systems/aspects", summary="Distinct system/aspect pairs")
def systems_aspects():
    c = Counter((r["system"], r["aspect"]) for r in SYS())
    return envelope("/api/v1/systems/aspects",
                    [{"system": s, "aspect": a, "record_count": n}
                     for (s, a), n in sorted(c.items())],
                    total=len(c))


@router.get("/api/v1/systems/ranks", summary="Ranked ladder tiers (reference)")
def systems_ranks():
    rows = load("ranked_ladder.csv", ref=True)
    return envelope("/api/v1/systems/ranks", rows, total=len(rows))


@router.get("/api/v1/systems/game-modes", summary="Game modes (reference)")
def systems_game_modes():
    rows = load("game_modes.csv", ref=True)
    return envelope("/api/v1/systems/game-modes", rows, total=len(rows))


@router.get("/api/v1/systems/battle-spells", summary="Battle spells with cooldowns (reference)")
def systems_battle_spells():
    rows = load("battle_spells.csv", ref=True)
    return envelope("/api/v1/systems/battle-spells", rows, total=len(rows))


@router.get("/api/v1/systems/emblems", summary="Current emblem sets (reference)")
def systems_emblems():
    rows = load("emblem_sets.csv", ref=True)
    return envelope("/api/v1/systems/emblems", rows, total=len(rows))


@router.get("/api/v1/systems/{system}", summary="Records for one system (Map, Ranking, Emblem, ...)")
def systems_by_name(system: str):
    rows = [r for r in SYS() if r["system"].lower() == system.lower()]
    if not rows:
        names = sorted({r["system"] for r in SYS()})
        raise HTTPException(404, detail=f"no system '{system}'; available: {names}")
    return envelope(f"/api/v1/systems/{system}", rows, total=len(rows))
