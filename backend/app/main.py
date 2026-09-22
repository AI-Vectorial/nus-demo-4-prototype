"""M04 Policy Assistant — backend API.

STEP 1 SCAFFOLD. A walking skeleton: enough to prove the deployment loop end to
end (branch -> PR -> CI -> human approval -> merge -> Railway) before any
retrieval or model code exists.

Retrieval, generation and persistence arrive in step 3, built through the
pipeline itself so the stage prompts are tested by the people who wrote them.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health

BUILD_SHA = os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")[:7]
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")

# The Next.js frontend is a separate Railway service, so it is cross-origin.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app = FastAPI(
    title="M04 Policy Assistant API",
    description="Ask questions about internal policy. Answers cite their sources.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

# Feature routers are mounted here by the tables during the lab.
# Each table owns exactly one module in app/features/ and one line below.
#
#   app.include_router(citations.router)   Table 1
#   app.include_router(history.router)     Table 2
#   app.include_router(guardrail.router)   Table 3
#   app.include_router(feedback.router)    Table 4
#   app.include_router(audit.router)       Table 5


@app.get("/")
async def root() -> dict[str, str]:
    """Service identity. The user-facing interface is the frontend service."""
    return {
        "service": "m04-policy-assistant-api",
        "version": "0.1.0",
        "build": BUILD_SHA,
        "environment": ENVIRONMENT,
        "docs": "/docs",
    }
