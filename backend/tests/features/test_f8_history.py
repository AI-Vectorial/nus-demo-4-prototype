"""F8 -- history. C19 and C20 at the API (REQ-C8, C9, A3, A6, U14)."""

from __future__ import annotations

import uuid

from app.core.models import Conversation
from tests.features.conftest import api

Q1 = "What approval thresholds apply to a travel expense claim?"
Q2 = "How long do we keep client correspondence records?"


def test_c19_conversations_are_listed_newest_first_with_a_title(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    older = client.post("/ask", json={"question": Q1}).json()
    newer = client.post("/ask", json={"question": Q2}).json()

    listed = client.get("/conversations").json()

    assert [c["id"] for c in listed] == [newer["conversation_id"], older["conversation_id"]]
    assert listed[0]["title"] == Q2
    assert listed[0]["message_count"] == 2
    assert listed[0]["started_at"] <= listed[0]["last_at"]


def test_c19_a_long_first_question_is_truncated_for_the_title(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    client.post("/ask", json={"question": "approval threshold " * 20})

    title = client.get("/conversations").json()[0]["title"]

    assert len(title) <= 81 and title.endswith("…")


def test_continuing_a_conversation_moves_it_to_the_top(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    older = client.post("/ask", json={"question": Q1}).json()
    client.post("/ask", json={"question": Q2})
    client.post("/ask", json={"question": Q2, "conversation_id": older["conversation_id"]})

    assert client.get("/conversations").json()[0]["id"] == older["conversation_id"]


def test_the_list_is_paginated(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    for _ in range(3):
        client.post("/ask", json={"question": Q1})

    page = client.get("/conversations", params={"limit": 2}).json()
    rest = client.get("/conversations", params={"limit": 2, "offset": 2}).json()

    assert len(page) == 2 and len(rest) == 1


def test_u14_a_conversation_with_no_turns_is_never_listed(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    with db() as s:
        s.add(Conversation())
        s.commit()

    assert client.get("/conversations").json() == []


def test_c20_opening_a_conversation_shows_its_turns_and_citations(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    asked = client.post("/ask", json={"question": Q1}).json()

    opened = client.get(f"/conversations/{asked['conversation_id']}").json()

    assert [m["role"] for m in opened["messages"]] == ["user", "assistant"]
    assert opened["messages"][0]["content"] == Q1
    answer = opened["messages"][1]
    assert answer["outcome"] == "answered" and answer["id"] == asked["message_id"]
    assert len(answer["citations"]) == len(asked["citations"])


def test_c20_an_opened_conversation_can_be_continued_with_its_context(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    asked = client.post("/ask", json={"question": Q1}).json()
    client.get(f"/conversations/{asked['conversation_id']}")

    client.post("/ask", json={"question": "And above that?",
                              "conversation_id": asked["conversation_id"]})

    assert model.embed_calls[-1] == [f"{Q1}\nAnd above that?"]


def test_an_unknown_conversation_is_not_found(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)

    assert client.get(f"/conversations/{uuid.uuid4()}").status_code == 404
