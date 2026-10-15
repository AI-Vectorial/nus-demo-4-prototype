"""POST /ask -- REQ-A1, REQ-A2."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.schemas import AskRequest, AskResponse
from app.core.database import get_session
from app.features import ask as exchange

log = logging.getLogger(__name__)
router = APIRouter()
Db = Annotated[Session, Depends(get_session)]


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, db: Db) -> AskResponse:
    try:
        result = exchange.answer(db, body.question, body.conversation_id)
    except exchange.ConversationNotFound as error:
        raise HTTPException(status_code=404, detail="conversation not found") from error
    except exchange.SearchUnavailable as error:
        # Nothing was recorded and nothing was answered. Say which part is down.
        log.error("search unavailable: %s", error)
        raise HTTPException(
            status_code=503,
            detail="the policy search is unavailable right now; nothing was recorded, try again",
        ) from error
    except SQLAlchemyError as error:
        # The exchange could not be recorded, so it is not answered either.
        log.error("could not record exchange: %s", type(error).__name__)
        raise HTTPException(
            status_code=503, detail="the exchange could not be recorded; try again"
        ) from error
    # One line per exchange (F6). Degraded is WARNING so a rising rate shows.
    (log.warning if result.outcome == "degraded" else log.info)(
        "exchange outcome=%s latency_ms=%d", result.outcome, result.latency_ms
    )
    return AskResponse(
        outcome=result.outcome,
        answer=result.answer,
        citations=result.citations,
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        latency_ms=result.latency_ms,
    )
