"""M-Series router — 7 endpoints."""
import re

from fastapi import APIRouter, HTTPException

from ..data import envelope, load

router = APIRouter(tags=["mseries"])

MS = lambda: load("mseries.csv")  # noqa: E731


def _edition(edition: str) -> dict:
    m = re.fullmatch(r"m(\d)", edition.lower())
    if m:
        n = m.group(1)
        for r in MS():
            if re.search(rf"\bM{n}\b", r["event"]):
                return r
    raise HTTPException(404, detail="edition not found; use m1..m8")


def _int(value: str):
    """Parse an integer from noisy strings like '5,680,511 (all-time record)'."""
    digits = re.sub(r"[^0-9]", "", str(value).split("(")[0])
    return int(digits) if digits else None


@router.get("/api/v1/mseries", summary="List M-Series world championship editions")
def mseries(limit: int = 50, offset: int = 0):
    rows = MS()
    page, total = paginate_local(rows, limit, offset)
    return envelope("/api/v1/mseries", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/mseries/latest", summary="Latest M-Series editions")
def mseries_latest():
    rows = [r for r in MS() if r["year"] == max(x["year"] for x in MS())]
    return envelope("/api/v1/mseries/latest", rows, total=len(rows))


@router.get("/api/v1/mseries/champions", summary="M-Series champions")
def mseries_champions():
    rows = [{"edition": r["event"], "year": r["year"], "champion": r["champion"],
             "runner_up": r["runner_up"], "finals_mvp": r["finals_mvp"],
             "prize_pool_usd": r["prize_pool_usd"]}
            for r in MS() if r["champion"]]
    return envelope("/api/v1/mseries/champions", rows, total=len(rows))


@router.get("/api/v1/mseries/viewership", summary="M-Series peak viewership")
def mseries_viewership():
    rows = [{"edition": r["event"], "year": r["year"], "peak_viewers": _int(r["peak_viewers"])}
            for r in MS()]
    rows.sort(key=lambda x: -(x["peak_viewers"] or 0))
    return envelope("/api/v1/mseries/viewership", rows, total=len(rows))


@router.get("/api/v1/mseries/prize-pools", summary="M-Series prize pools (USD)")
def mseries_prize_pools():
    rows = [{"edition": r["event"], "year": r["year"],
             "prize_pool_usd": _int(r["prize_pool_usd"])}
            for r in MS() if _int(r["prize_pool_usd"])]
    rows.sort(key=lambda x: x["year"])
    return envelope("/api/v1/mseries/prize-pools", rows, total=len(rows))


@router.get("/api/v1/mseries/hosts", summary="M-Series host cities and countries")
def mseries_hosts():
    rows = [{"edition": r["event"], "year": r["year"], "host_city": r["host_city"],
             "host_country": r["host_country"], "dates": r["dates"], "teams": r["teams_count"]}
            for r in MS()]
    return envelope("/api/v1/mseries/hosts", rows, total=len(rows))


@router.get("/api/v1/mseries/{edition}", summary="One M-Series edition (m1..m8)")
def mseries_edition(edition: str):
    return envelope(f"/api/v1/mseries/{edition}", _edition(edition))


def paginate_local(rows, limit, offset):
    return rows[offset: offset + limit], len(rows)
