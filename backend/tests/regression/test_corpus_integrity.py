"""The corpus is a contract, and these are the properties it must keep.

Every one of these exists because something downstream depends on it. A corpus
that silently loses its superseded version, or its conflict, or its gap, still
looks fine -- and the behaviour it was there to demonstrate quietly stops
working.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CORPUS = Path(__file__).resolve().parents[2] / "corpus"
POLICIES = sorted(
    p for p in CORPUS.glob("*.md") if p.stem not in {"EVALUATION", "FICTION-AUDIT"}
)


def front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{path.name} has no front matter"
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


# --------------------------------------------------------------------------- shape


def test_the_corpus_is_not_empty():
    assert len(POLICIES) == 5


@pytest.mark.parametrize("path", POLICIES, ids=lambda p: p.stem)
def test_every_document_has_complete_front_matter(path: Path):
    fields = front_matter(path)
    for required in ("id", "title", "version", "effective", "owner", "status"):
        assert fields.get(required), f"{path.name} is missing {required}"


@pytest.mark.parametrize("path", POLICIES, ids=lambda p: p.stem)
def test_status_is_one_of_two_values(path: Path):
    assert front_matter(path)["status"] in {"current", "superseded"}


@pytest.mark.parametrize("path", POLICIES, ids=lambda p: p.stem)
def test_headings_are_unique_within_a_document(path: Path):
    """A citation names a section. Two sections with one name is ambiguous."""
    headings = re.findall(r"^#{2,3} (.+)$", path.read_text(encoding="utf-8"), re.M)
    duplicates = {h for h in headings if headings.count(h) > 1}
    assert not duplicates, f"{path.name} repeats: {duplicates}"


@pytest.mark.parametrize("path", POLICIES, ids=lambda p: p.stem)
def test_every_document_is_listed_in_the_manifest(path: Path):
    manifest = (CORPUS / "MANIFEST.yaml").read_text(encoding="utf-8")
    assert path.name in manifest, f"{path.name} is not in MANIFEST.yaml"


# ------------------------------------------------------- the deliberate properties


def test_one_policy_exists_in_two_versions():
    """REQ-I7 and D4. Without this, "has this changed?" is unanswerable."""
    statuses = [front_matter(p)["status"] for p in POLICIES]
    assert statuses.count("superseded") == 1
    assert statuses.count("current") == 4


def test_the_two_versions_disagree_about_the_threshold():
    """The point of keeping both. If they matched, the question would be moot."""
    current = next(p for p in POLICIES if p.stem.endswith("v3.1")).read_text(encoding="utf-8")
    old = next(p for p in POLICIES if p.stem.endswith("v3.0")).read_text(encoding="utf-8")

    assert "£75 or more" in current
    assert "£50 or more" in old


def test_the_threshold_is_stated_as_inclusive():
    """Where M04 Lab 17's planted defect lives.

    An implementation using > rather than >= passes every other question in the
    evaluation set and fails at exactly this boundary.
    """
    text = next(p for p in POLICIES if p.stem.endswith("v3.1")).read_text(encoding="utf-8")
    assert "exactly £75 requires line-manager approval" in text


def test_the_retention_conflict_still_exists():
    """D6. Two current policies that cannot both be satisfied."""
    retention_doc = next(p for p in POLICIES if "records-retention" in p.stem)
    outsourcing_doc = next(p for p in POLICIES if "outsourcing" in p.stem)
    retention = retention_doc.read_text(encoding="utf-8")
    outsourcing = outsourcing_doc.read_text(encoding="utf-8")

    assert "7 years" in retention
    assert "End of the client relationship" in retention
    assert "within five years" in outsourcing
    assert front_matter(retention_doc)["status"] == "current"
    assert front_matter(outsourcing_doc)["status"] == "current"


def test_the_conflict_is_escalated_not_resolved():
    """The corpus must not decide it -- that is the whole of D6."""
    doc = next(p for p in POLICIES if "outsourcing" in p.stem)
    assert "Do not resolve the conflict locally" in doc.read_text(encoding="utf-8")


def test_the_travel_policy_is_silent_on_a_partner_travelling():
    """The refusal case. If the travel policy gains a rule here, Q11 stops working.

    Scoped to the travel documents deliberately. The KYC policy says "immediate
    family member" about politically exposed persons, which is a different
    subject entirely -- an earlier version of this test searched the whole
    corpus and failed on it, which is a test being blunt rather than a corpus
    being wrong.
    """
    travel = [p for p in POLICIES if "travel-expense" in p.stem]
    assert travel, "the travel policy is missing"

    for path in travel:
        text = path.read_text(encoding="utf-8").lower()
        for word in ("spouse", "dependant", "partner", "family member"):
            assert word not in text, (
                f"{path.name} now mentions {word!r} -- EVALUATION.md Q11 expects "
                "the travel policy to be silent on who else may travel"
            )


# ------------------------------------------------------------------- it stays fictional


@pytest.mark.parametrize("path", POLICIES, ids=lambda p: p.stem)
def test_no_real_institution_appears(path: Path):
    """A fictional bank citing a real institution stops being fictional."""
    text = path.read_text(encoding="utf-8")
    real = [
        "MUFG", "Mitsubishi", "HSBC", "Barclays", "Lloyds", "NatWest", "Santander",
        "Citibank", "JPMorgan", "Goldman", "Deutsche", "UBS", "Credit Suisse",
        "Standard Chartered", "DBS", "OCBC", "Nomura", "Mizuho",
        "FCA", "PRA", "MAS", "FINRA", "BaFin", "JFSA",
    ]
    found = [n for n in real if re.search(rf"\b{re.escape(n)}\b", text)]
    assert not found, f"{path.name} names: {found}"


@pytest.mark.parametrize("path", POLICIES, ids=lambda p: p.stem)
def test_every_document_says_it_is_fictional(path: Path):
    assert "fictional" in path.read_text(encoding="utf-8").lower()
