"""F7 -- the corpus API. Criteria C16, C17 at the API; C18 and C26 are in the UI.

Documents are read from backend/corpus/, never copied into the database (REQ-B5).
"""

from __future__ import annotations


def test_c16_the_list_has_all_five_documents_with_their_metadata(client):
    documents = client.get("/corpus").json()

    assert len(documents) == 5
    for d in documents:
        assert {"id", "title", "owner", "version", "effective", "status", "sections"} <= set(d)
    assert {(d["id"], d["version"], d["status"]) for d in documents} >= {
        ("travel-expense-policy", "3.1", "current"),
        ("travel-expense-policy", "3.0", "superseded"),
    }


def test_c17_a_document_shows_its_sections_and_their_text(client):
    document = client.get("/corpus/records-retention").json()

    headings = [s["heading"] for s in document["sections"]]
    assert "4.1 General table" in headings
    table = next(s for s in document["sections"] if s["heading"] == "4.1 General table")
    assert "|" in table["text"]  # the Markdown table arrives intact, for the UI to render


def test_the_current_version_is_the_default(client):
    assert client.get("/corpus/travel-expense-policy").json()["version"] == "3.1"


def test_a_version_can_be_asked_for_so_a_superseded_citation_opens_its_own_text(client):
    document = client.get("/corpus/travel-expense-policy", params={"version": "3.0"}).json()

    assert document["status"] == "superseded"
    assert any(s["heading"] == "4.1 Approval thresholds" for s in document["sections"])


def test_an_unknown_document_is_not_found(client):
    assert client.get("/corpus/no-such-policy").status_code == 404
    assert client.get("/corpus/travel-expense-policy",
                      params={"version": "9.9"}).status_code == 404
