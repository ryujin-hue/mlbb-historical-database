"""Reference router — 11 endpoints over references/ lookup tables."""
from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, load, paginate, reference_tables

router = APIRouter(tags=["reference"])

ALIASES = {
    "roles": "hero_roles",
    "lanes": "hero_lanes",
    "lore-regions": "lore_regions",
    "battle-spells": "battle_spells",
    "emblem-sets": "emblem_sets",
    "ranked-ladder": "ranked_ladder",
    "game-modes": "game_modes",
    "change-types": "change_types",
    "host-countries": "host_countries",
}


def _table(key: str) -> str:
    name = ALIASES.get(key, key)
    if name not in reference_tables():
        raise HTTPException(404, detail=f"reference table not found: {key}; "
                                        f"available: {reference_tables()}")
    return name


@router.get("/api/v1/reference", summary="List reference tables")
def reference_index():
    rows = [{"table": t, "endpoint": f"/api/v1/reference/{ALIASES.get(t, t)}",
             "row_count": len(load(f"{t}.csv", ref=True))}
            for t in reference_tables()]
    return envelope("/api/v1/reference", rows, total=len(rows))


@router.get("/api/v1/reference/roles", summary="Hero roles (reference)")
def ref_roles():
    rows = load("hero_roles.csv", ref=True)
    return envelope("/api/v1/reference/roles", rows, total=len(rows))


@router.get("/api/v1/reference/lanes", summary="Hero lanes (reference)")
def ref_lanes():
    rows = load("hero_lanes.csv", ref=True)
    return envelope("/api/v1/reference/lanes", rows, total=len(rows))


@router.get("/api/v1/reference/lore-regions", summary="Lore regions (reference)")
def ref_lore_regions():
    rows = load("lore_regions.csv", ref=True)
    return envelope("/api/v1/reference/lore-regions", rows, total=len(rows))


@router.get("/api/v1/reference/battle-spells", summary="Battle spells (reference)")
def ref_battle_spells():
    rows = load("battle_spells.csv", ref=True)
    return envelope("/api/v1/reference/battle-spells", rows, total=len(rows))


@router.get("/api/v1/reference/emblem-sets", summary="Emblem sets (reference)")
def ref_emblem_sets():
    rows = load("emblem_sets.csv", ref=True)
    return envelope("/api/v1/reference/emblem-sets", rows, total=len(rows))


@router.get("/api/v1/reference/ranked-ladder", summary="Ranked ladder (reference)")
def ref_ranked_ladder():
    rows = load("ranked_ladder.csv", ref=True)
    return envelope("/api/v1/reference/ranked-ladder", rows, total=len(rows))


@router.get("/api/v1/reference/game-modes", summary="Game modes (reference)")
def ref_game_modes():
    rows = load("game_modes.csv", ref=True)
    return envelope("/api/v1/reference/game-modes", rows, total=len(rows))


@router.get("/api/v1/reference/change-types", summary="Change-type taxonomy (reference)")
def ref_change_types():
    rows = load("change_types.csv", ref=True)
    return envelope("/api/v1/reference/change-types", rows, total=len(rows))


@router.get("/api/v1/reference/host-countries", summary="Event host countries (reference)")
def ref_host_countries():
    rows = load("host_countries.csv", ref=True)
    return envelope("/api/v1/reference/host-countries", rows, total=len(rows))


@router.get("/api/v1/reference/{table}", summary="Generic access to any reference table")
def ref_table(table: str):
    name = _table(table)
    rows = load(f"{name}.csv", ref=True)
    return envelope(f"/api/v1/reference/{table}", rows, total=len(rows))
