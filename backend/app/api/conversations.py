"""GET /conversations and GET /conversations/{id} -- REQ-A3, REQ-A6."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import ConversationSummary, ConversationView
from app.core.database import get_session
from app.features import history

router = APIRouter()
Db = Annotated[Session, Depends(get_session)]


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    db: Db,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    return history.list_conversations(db, limit=limit, offset=offset)


@router.get("/conversations/{conversation_id}", response_model=ConversationView)
def get_conversation(conversation_id: uuid.UUID, db: Db) -> dict:
    found = history.get_conversation(db, conversation_id)
    if found is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    return found
