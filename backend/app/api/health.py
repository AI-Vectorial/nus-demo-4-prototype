"""Health and deployment-validation endpoints.

Railway polls /healthz before routing traffic to a new deployment, and the
post-deploy smoke test asserts against it.  It reports build identity so that a
failed rollout is distinguishable from a stale one -- "it works on my machine is
not a release" made checkable.  [M04.5]
"""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter(tags=["ops"])

BUILD_SHA = os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7]
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")


@router.get("/healthz")
async def healthz() -> dict:
    return {
        "status": "ok",
        "build": BUILD_SHA,
        "environment": ENVIRONMENT,
        "dependencies": {
            # Populated in step 3 when the corpus, vector store and model
            # client exist.  Until then they are honestly reported as absent
            # rather than quietly omitted.
            "database": "not_configured",
            "vector_store": "not_configured",
            "model": "not_configured",
        },
    }
