"""Esports router — 7 endpoints (MSC/EWC/MWI/MPL events)."""
from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, first_year, load, paginate

router = APIRouter(tags=["esports"])

EV = lambda: load("esports.csv")  # noqa: E731


@router.get("/api/v1/esports", summary="List esports event records")
def esports(region: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = EV()
    if region:
        rows = [r for r in rows if region.lower() in r["region"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/esports", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/esports/regions", summary="Distinct regions with counts")
def esports_regions():
    c = Counter(r["region"] for r in EV())
    return envelope("/api/v1/esports/regions",
                    [{"region": k, "event_count": v} for k, v in c.most_common()],
                    total=len(c))


@router.get("/api/v1/esports/region/{region}", summary="Events in a region")
def esports_region(region: str):
    rows = [r for r in EV() if region.lower() in r["region"].lower()]
    if not rows:
        raise HTTPException(404, detail=f"no events for region {region}")
    return envelope(f"/api/v1/esports/region/{region}", rows, total=len(rows))


@router.get("/api/v1/esports/year/{year}", summary="Events by calendar year (MPL rows use seasons)")
def esports_year(year: str):
    rows = [r for r in EV() if year in r["season"] or year in r["dates"]]
    if not rows:
        raise HTTPException(404, detail=(f"no events in {year}; "
                                         "MPL Philippines rows are keyed by season (S1-S18)"))
    return envelope(f"/api/v1/esports/year/{year}", rows, total=len(rows))


@router.get("/api/v1/esports/champions", summary="Champions grouped by titles")
def esports_champions():
    champs = Counter(r["champion"] for r in EV() if r["champion"])
    rows = [{"champion": k, "titles": v}
            for k, v in champs.most_common()]
    return envelope("/api/v1/esports/champions", rows, total=len(rows))


@router.get("/api/v1/esports/prize-pools", summary="Events with recorded prize pools")
def esports_prize_pools():
    rows = [{"event": r["event"], "region": r["region"], "season": r["season"],
             "prize_pool_usd": r["prize_pool_usd"]}
            for r in EV() if r["prize_pool_usd"].strip()]
    return envelope("/api/v1/esports/prize-pools", rows, total=len(rows))


@router.get("/api/v1/esports/event-types", summary="Tournament event types (reference)")
def esports_event_types():
    rows = load("tournament_event_types.csv", ref=True)
    return envelope("/api/v1/esports/event-types", rows, total=len(rows))
