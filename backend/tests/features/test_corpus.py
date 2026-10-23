from __future__ import annotations

from pathlib import Path


def write_corpus(directory: Path) -> None:
    directory.mkdir()
    (directory / "MANIFEST.yaml").write_text(
        """documents:
  - id: travel-policy
    file: travel-v2.md
    title: Travel Policy
    version: "2.0"
    effective: 2026-01-01
    owner: Group Finance
    status: current
  - id: travel-policy
    file: travel-v1.md
    title: Travel Policy
    version: "1.0"
    effective: 2025-01-01
    owner: Group Finance
    status: superseded
""",
        encoding="utf-8",
    )
    for filename, version, effective, status in (
        ("travel-v2.md", "2.0", "2026-01-01", "current"),
        ("travel-v1.md", "1.0", "2025-01-01", "superseded"),
    ):
        (directory / filename).write_text(
            f"""---
id: travel-policy
title: Travel Policy
version: "{version}"
effective: {effective}
owner: Group Finance
status: {status}
---

# Travel Policy

## 4.2 Approval

Claims over the configured limit require approval.
""",
            encoding="utf-8",
        )


def test_corpus_list_includes_version_metadata_and_superseded_status(
    client, tmp_path: Path, monkeypatch
) -> None:
    from app.api import corpus

    write_corpus(tmp_path / "corpus")
    monkeypatch.setattr(corpus, "CORPUS_DIR", tmp_path / "corpus")

    response = client.get("/corpus")

    assert response.status_code == 200
    documents = response.json()["documents"]
    assert len(documents) == 2
    assert {item["version"] for item in documents} == {"1.0", "2.0"}
    assert all(item["owner"] == "Group Finance" for item in documents)
    assert {item["status"] for item in documents} == {"current", "superseded"}
    assert {item["effective"] for item in documents} == {"2025-01-01", "2026-01-01"}


def test_corpus_detail_selects_exact_version_and_returns_markdown(
    client, tmp_path: Path, monkeypatch
) -> None:
    from app.api import corpus

    write_corpus(tmp_path / "corpus")
    monkeypatch.setattr(corpus, "CORPUS_DIR", tmp_path / "corpus")

    response = client.get("/corpus/travel-policy?version=1.0")

    assert response.status_code == 200
    document = response.json()
    assert document["version"] == "1.0"
    assert document["status"] == "superseded"
    assert "## 4.2 Approval" in document["content"]
    assert "Claims over the configured limit require approval." in document["content"]


def test_corpus_detail_defaults_to_current_and_unknown_document_is_404(
    client, tmp_path: Path, monkeypatch
) -> None:
    from app.api import corpus

    write_corpus(tmp_path / "corpus")
    monkeypatch.setattr(corpus, "CORPUS_DIR", tmp_path / "corpus")

    current = client.get("/corpus/travel-policy")
    missing = client.get("/corpus/not-a-policy")

    assert current.status_code == 200
    assert current.json()["version"] == "2.0"
    assert missing.status_code == 404
