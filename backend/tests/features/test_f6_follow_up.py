"""F6 -- follow-ups. C14 and C15 at the API (D8, D9); C31 is measured on the
real model and reported, not asserted here, because it does not pass.
"""

from __future__ import annotations

from tests.features.conftest import api

FIRST = "What approval thresholds apply to a travel expense claim?"
FOLLOW_UP = "What about expenses above that limit?"


def test_c14_retrieval_runs_again_on_the_follow_up(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    first = client.post("/ask", json={"question": FIRST}).json()
    searches = len(model.embed_calls)

    client.post("/ask", json={"question": FOLLOW_UP, "conversation_id": first["conversation_id"]})

    assert len(model.embed_calls) == searches + 1


def test_c14_d9_the_follow_up_is_searched_with_the_question_before_it(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    first = client.post("/ask", json={"question": FIRST}).json()

    client.post("/ask", json={"question": FOLLOW_UP, "conversation_id": first["conversation_id"]})

    assert model.embed_calls[-1] == [f"{FIRST}\n{FOLLOW_UP}"]


def test_d9_the_assistant_answer_is_never_part_of_the_search(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    first = client.post("/ask", json={"question": FIRST}).json()

    client.post("/ask", json={"question": FOLLOW_UP, "conversation_id": first["conversation_id"]})

    assert model.answer not in model.embed_calls[-1][0]


def test_c14_d8_the_answer_sees_the_recent_turns(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    first = client.post("/ask", json={"question": FIRST}).json()

    client.post("/ask", json={"question": FOLLOW_UP, "conversation_id": first["conversation_id"]})

    prompt = model.generate_calls[-1]["prompt"]
    assert f"User: {FIRST}" in prompt
    assert f"Assistant: {model.answer}" in prompt
    assert f"Question: {FOLLOW_UP}" in prompt


def test_d8_only_the_last_five_messages_are_in_the_window(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    cid = None
    for n in range(4):
        cid = client.post("/ask", json={"question": f"Approval threshold question {n}",
                                        "conversation_id": cid}).json()["conversation_id"]

    client.post("/ask", json={"question": FOLLOW_UP, "conversation_id": cid})

    # 8 stored messages + the new question; the window keeps the last 5:
    # Q2, A2, Q3, A3, and the follow-up. Searched on the user questions in it.
    assert model.embed_calls[-1] == [
        f"Approval threshold question 2\nApproval threshold question 3\n{FOLLOW_UP}"
    ]


def test_c15_a_new_conversation_has_no_prior_context_and_history_is_kept(db, indexed, model):
    client = api(db, indexed, embed=model.embed, generate=model.generate)
    first = client.post("/ask", json={"question": FIRST}).json()

    fresh = client.post("/ask", json={"question": FOLLOW_UP}).json()

    assert fresh["conversation_id"] != first["conversation_id"]
    assert model.embed_calls[-1] == [FOLLOW_UP]
    assert client.get(f"/conversations/{first['conversation_id']}").status_code == 200
