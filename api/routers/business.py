"""Business router — 4 endpoints (Moonton/business records)."""
from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, load, paginate

router = APIRouter(tags=["business"])

BIZ = lambda: load("business.csv")  # noqa: E731


@router.get("/api/v1/business", summary="List business/Moonton records")
def business(topic: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = BIZ()
    if topic:
        rows = [r for r in rows if topic.lower() == r["topic"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/business", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/business/topics", summary="Distinct topics with counts")
def business_topics():
    c = Counter(r["topic"] for r in BIZ())
    return envelope("/api/v1/business/topics",
                    [{"topic": k, "record_count": v} for k, v in c.most_common()],
                    total=len(c))


@router.get("/api/v1/business/topic/{topic}", summary="Records for one topic")
def business_topic(topic: str):
    rows = [r for r in BIZ() if r["topic"].lower() == topic.lower()]
    if not rows:
        topics = sorted({r["topic"] for r in BIZ()})
        raise HTTPException(404, detail=f"no topic '{topic}'; available: {topics}")
    return envelope(f"/api/v1/business/topic/{topic}", rows, total=len(rows))


@router.get("/api/v1/business/ownership", summary="Moonton ownership history")
def business_ownership():
    rows = [r for r in BIZ() if r["topic"].lower() == "ownership"]
    return envelope("/api/v1/business/ownership", rows, total=len(rows))
