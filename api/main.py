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
    """Count the public GET endpoints defined by this API (78 expected)."""
    from fastapi.routing import APIRoute
    return sum(1 for r in app.routes
               if isinstance(r, APIRoute) and "GET" in r.methods)
