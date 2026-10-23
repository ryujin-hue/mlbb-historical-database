"""Client router — 4 endpoints (client/platform/collab records)."""
from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, load, paginate

router = APIRouter(tags=["client"])

CL = lambda: load("client.csv")  # noqa: E731


@router.get("/api/v1/client", summary="List client/platform records")
def client(aspect: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = CL()
    if aspect:
        rows = [r for r in rows if aspect.lower() == r["aspect"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/client", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/client/aspects", summary="Distinct aspects with counts")
def client_aspects():
    c = Counter(r["aspect"] for r in CL())
    return envelope("/api/v1/client/aspects",
                    [{"aspect": k, "record_count": v} for k, v in c.most_common()],
                    total=len(c))


@router.get("/api/v1/client/aspect/{aspect}", summary="Records for one aspect")
def client_aspect(aspect: str):
    rows = [r for r in CL() if r["aspect"].lower() == aspect.lower()]
    if not rows:
        aspects = sorted({r["aspect"] for r in CL()})
        raise HTTPException(404, detail=f"no aspect '{aspect}'; available: {aspects}")
    return envelope(f"/api/v1/client/aspect/{aspect}", rows, total=len(rows))


@router.get("/api/v1/client/collabs", summary="All collaboration/crossover records")
def client_collabs():
    rows = [r for r in CL() if r["aspect"].lower() == "collab"]
    return envelope("/api/v1/client/collabs", rows, total=len(rows))
