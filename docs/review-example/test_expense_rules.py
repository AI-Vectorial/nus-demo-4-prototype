"""Tests for the expense approval rules.

These all pass.
"""

from __future__ import annotations

from expense_rules import Claim, is_auto_approved, required_approvals


def claim(amount: float) -> Claim:
    return Claim(
        id="c-1",
        amount_gbp=amount,
        category="travel",
        claimant_name="A. Claimant",
        claimant_email="a.claimant@aldermere.example",
    )


def test_a_small_claim_is_automatic():
    assert is_auto_approved(claim(40.00))


def test_a_larger_claim_needs_a_line_manager():
    assert required_approvals(claim(120.00)) == ["line_manager"]


def test_five_hundred_needs_a_department_head():
    assert required_approvals(claim(500.00)) == ["line_manager", "department_head"]


def test_a_very_large_claim_needs_group_finance():
    assert required_approvals(claim(3000.00)) == [
        "line_manager",
        "department_head",
        "group_finance",
    ]
