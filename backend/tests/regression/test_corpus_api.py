"""The corpus browser -- F7, REQ-B1 to REQ-B5 and REQ-A4.

These read the real corpus, on purpose. /corpus serves the files in
backend/corpus/ at request time, and a test against a fixture would not notice
if that stopped being true.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

EXPECTED_IDS = {
    "travel-expense-policy",
    "client-onboarding-kyc",
    "records-retention",
    "outsourcing-third-party",
}


def test_corpus_lists_every_document(client: TestClient) -> None:
    """Five files, four ids -- travel expense is published twice."""
    body = client.get("/corpus").json()
    assert len(body) == 5
    assert {document["id"] for document in body} == EXPECTED_IDS


def test_every_document_carries_its_metadata(client: TestClient) -> None:
    """REQ-B1: title, owner, version, effective date and status."""
    for document in client.get("/corpus").json():
        assert document["title"]
        assert document["owner"]
        assert document["version"]
        assert document["effective"]
        assert document["status"] in {"current", "superseded"}


def test_a_superseded_document_is_listed_not_hidden(client: TestClient) -> None:
    """REQ-B2 / D4: shown and flagged, so "is this still current?" is answerable."""
    statuses = {
        (document["id"], document["version"]): document["status"]
        for document in client.get("/corpus").json()
    }
    assert statuses[("travel-expense-policy", "3.1")] == "current"
    assert statuses[("travel-expense-policy", "3.0")] == "superseded"


def test_the_list_carries_section_headings(client: TestClient) -> None:
    """Headings only in the list -- the text belongs to the detail view."""
    documents = {
        document["version"]: document
        for document in client.get("/corpus").json()
        if document["id"] == "travel-expense-policy"
    }
    sections = documents["3.1"]["sections"]
    assert "4.2 Approval thresholds" in sections
    assert sections.index("4.1 General principle") < sections.index("4.2 Approval thresholds")


def test_a_document_serves_its_section_text(client: TestClient) -> None:
    """REQ-B3: the section a citation points at can be read."""
    body = client.get("/corpus/travel-expense-policy").json()
    approval = next(s for s in body["sections"] if s["heading"] == "4.2 Approval thresholds")
    assert "75" in approval["text"]


def test_a_document_defaults_to_the_current_version(client: TestClient) -> None:
    """One id, two files: a citation link must land on the policy in force."""
    body = client.get("/corpus/travel-expense-policy").json()
    assert body["version"] == "3.1"
    assert body["status"] == "current"
    assert body["owner"] == "Group Finance"


def test_the_superseded_version_is_selectable(client: TestClient) -> None:
    """REQ-I7's browsing half: the withdrawn threshold is still readable."""
    body = client.get("/corpus/travel-expense-policy", params={"version": "3.0"}).json()
    assert body["version"] == "3.0"
    assert body["status"] == "superseded"
    # The threshold moved from 50 to 75 -- and in 3.0 it lived in 4.1.
    approval = next(s for s in body["sections"] if s["heading"] == "4.1 Approval thresholds")
    assert "50" in approval["text"]


def test_an_unknown_document_is_404(client: TestClient) -> None:
    assert client.get("/corpus/no-such-policy").status_code == 404


def test_an_unknown_version_is_404(client: TestClient) -> None:
    assert client.get("/corpus/travel-expense-policy", params={"version": "9.9"}).status_code == 404


def test_the_manifest_is_not_served_as_a_policy(client: TestClient) -> None:
    """MANIFEST.yaml and EVALUATION.md share the directory. Neither is policy."""
    titles = {document["title"] for document in client.get("/corpus").json()}
    assert "Evaluation set" not in titles
