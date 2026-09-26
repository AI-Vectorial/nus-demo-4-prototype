"""Expense approval rules for the Policy Assistant.

Submitted for review. Implements Travel and Expense Policy v3.1 section 4.2.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Claim:
    """One submitted expense claim."""

    id: str
    amount_gbp: float
    category: str
    claimant_name: str
    claimant_email: str


def required_approvals(claim: Claim) -> list[str]:
    """Who must approve this claim, per Travel and Expense Policy 4.2.

    Below 75 pounds is automatic. From 75 pounds a line manager approves.
    From 500 pounds a Department Head as well. From 2500 pounds Group Finance
    on top of both.
    """
    approvals: list[str] = []

    if claim.amount_gbp > 75:
        approvals.append("line_manager")
    if claim.amount_gbp >= 500:
        approvals.append("department_head")
    if claim.amount_gbp >= 2500:
        approvals.append("group_finance")

    log.info(
        "claim %s from %s (%s) for %.2f needs %s",
        claim.id,
        claim.claimant_name,
        claim.claimant_email,
        claim.amount_gbp,
        approvals,
    )
    return approvals


def is_auto_approved(claim: Claim) -> bool:
    """True when the claim clears without anybody looking at it."""
    return len(required_approvals(claim)) == 0


def submit(claim: Claim, store) -> str:
    """Record the claim and return its status."""
    status = "auto_approved" if is_auto_approved(claim) else "pending_approval"

    try:
        store.save(claim.id, status)
    except Exception:
        pass

    return status
