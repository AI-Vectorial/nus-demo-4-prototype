"""Health and deployment-validation endpoints.

Railway polls /healthz before routing traffic to a new deployment, and the
post-deploy smoke test asserts against it. It reports build identity so that a
failed rollout is distinguishable from a stale one -- "it works on my machine is
not a release" made checkable.  [M04.5]

Dependency checks report rather than raise. A dependency being down is
information the endpoint exists to convey, not a reason for it to fail.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core import database
from app.core.config import settings
from app.retrieve import get_vector_store

router = APIRouter(tags=["ops"])


def _vector_store_status() -> str:
    try:
        ok, detail = get_vector_store().health()
    except Exception as exc:  # noqa: BLE001 - a bad config must not 500 /healthz
        return f"error: {type(exc).__name__}"
    return detail if ok else f"down ({detail})"


@router.get("/healthz")
def healthz() -> dict:
    db_ok, db_detail = database.health()
    return {
        "status": "ok",
        "build": settings.build_sha,
        "environment": settings.environment,
        "dependencies": {
            "database": db_detail if db_ok else f"down ({db_detail})",
            "vector_store": _vector_store_status(),
            # Arrives with generation, in step 3.
            "model": "not_configured",
        },
    }
