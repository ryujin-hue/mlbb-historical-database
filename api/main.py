"""FastAPI application exposing the MLBB Historical Database.

Exactly 78 GET endpoints (11 routers + the index route). All data is served
from the repository's CSV files — no external calls at request time.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import __version__
from .data import BASE_DIR, DESCRIPTION
from .routers import (business, client, esports, extras, heroes, items, meta,
                      mseries, patches, reference, systems)

app = FastAPI(
    title="MLBB Historical Database API",
    version=__version__,
    description=DESCRIPTION + "\n\nSource repo: https://github.com/ryujin-hue/mlbb-historical-database",
    docs_url="/docs",
)

app.include_router(meta.router)
app.include_router(heroes.router)
app.include_router(extras.router)
app.include_router(items.router)
app.include_router(patches.router)
app.include_router(mseries.router)
app.include_router(esports.router)
app.include_router(systems.router)
app.include_router(client.router)
app.include_router(business.router)
app.include_router(reference.router)

# Repo images (heroes, items, emblems, spells, events, teams) served statically.
app.mount("/img", StaticFiles(directory=BASE_DIR / "images"), name="images")


def count_api_routes() -> int:
    """Count the public GET endpoints defined by this API (78 expected).

    Counts via the generated OpenAPI schema instead of introspecting
    app.routes: FastAPI >= 0.160 (Starlette 1.x) keeps included routers
    nested, so isinstance(r, APIRoute) no longer finds included endpoints,
    while the OpenAPI contract is stable across all FastAPI versions.
    """
    paths = app.openapi().get("paths", {})
    return sum(1 for ops in paths.values() if "get" in ops)
