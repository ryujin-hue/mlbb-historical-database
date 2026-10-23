"""Items router — 8 endpoints (master shop + change history)."""
from fastapi import APIRouter, HTTPException, Query

from ..data import envelope, first_year, load, paginate, slugify, with_image_url

router = APIRouter(tags=["items"])

ITEMS = lambda: with_image_url(load("items_master.csv"))  # noqa: E731
CHANGES = lambda: with_image_url(load("item_changes.csv"))  # noqa: E731


def _find(item: str) -> dict:
    target = slugify(item)
    for i in ITEMS():
        if slugify(i["item"]) == target:
            return i
    raise HTTPException(404, detail=f"item not found: {item}")


@router.get("/api/v1/items", summary="List current-shop items")
def items(category: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = ITEMS()
    if category:
        rows = [i for i in rows if category.lower() in i["category"].lower()]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/items", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/items/count", summary="Item count")
def items_count():
    cats = sorted({i["category"] for i in ITEMS()})
    return envelope("/api/v1/items/count", {"total": len(ITEMS()), "categories": cats})


@router.get("/api/v1/items/search", summary="Search items by name/passive")
def items_search(q: str, limit: int = Query(20, le=100)):
    q = q.lower()
    hits = [i for i in ITEMS() if q in i["item"].lower() or q in (i.get("unique_passives") or "").lower()]
    return envelope("/api/v1/items/search", hits[:limit], total=len(hits))


@router.get("/api/v1/items/category/{category}", summary="Items by category")
def items_category(category: str):
    rows = [i for i in ITEMS() if category.lower() == i["category"].lower()]
    if not rows:
        cats = sorted({i["category"] for i in ITEMS()})
        raise HTTPException(404, detail=f"no category '{category}'; available: {cats}")
    return envelope(f"/api/v1/items/category/{category}", rows, total=len(rows))


@router.get("/api/v1/items/changes", summary="All item/equipment changes")
def items_changes(change_type: str | None = None, version: str | None = None,
                  year: str | None = None, limit: int = Query(50, le=1000), offset: int = 0):
    rows = CHANGES()
    if change_type:
        rows = [r for r in rows if r["change_type"].lower() == change_type.lower()]
    if version:
        rows = [r for r in rows if r["version"].lower() == version.lower()]
    if year:
        rows = [r for r in rows if first_year(r["date"]) == year]
    page, total = paginate(rows, limit, offset)
    return envelope("/api/v1/items/changes", page, total=total, limit=limit, offset=offset)


@router.get("/api/v1/items/changes/type/{change_type}", summary="Item changes by type")
def items_changes_type(change_type: str, limit: int = Query(50, le=1000), offset: int = 0):
    rows = [r for r in CHANGES() if r["change_type"].lower() == change_type.lower()]
    if not rows:
        raise HTTPException(404, detail=f"no item changes of type {change_type}")
    page, total = paginate(rows, limit, offset)
    return envelope(f"/api/v1/items/changes/type/{change_type}", page,
                    total=total, limit=limit, offset=offset)


@router.get("/api/v1/items/changes/patch/{version}", summary="Item changes in a patch")
def items_changes_patch(version: str):
    rows = [r for r in CHANGES() if r["version"].lower() == version.lower()]
    if not rows:
        raise HTTPException(404, detail=f"no item changes recorded for patch {version}")
    return envelope(f"/api/v1/items/changes/patch/{version}", rows, total=len(rows))


@router.get("/api/v1/items/{item}", summary="Item detail")
def item_detail(item: str):
    return envelope(f"/api/v1/items/{item}", _find(item))
