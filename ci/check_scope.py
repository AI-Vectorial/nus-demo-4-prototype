#!/usr/bin/env python3
"""Scope check — the mechanical enforcement of a permission boundary.

M04.3 teaches that "protected files, external access and destructive actions are
where autonomy stops and a human decides", and its Demo Brief requires one change
that is *genuinely rejected* — "checkable, not narrated".

This is that check. It fails the build when a diff touches a protected path, or
when a table's branch strays outside the files that table owns.

The interesting property: the agent will already have been told no once, by a
human, during plan review. When it reaches for a protected file anyway, this
catches what the room missed.
"""

from __future__ import annotations

import re
import subprocess
import sys

# Paths nobody may change during the lab. The pipeline, the gates and the
# context pack are the lesson; an agent editing them to make its life easier is
# precisely the failure mode being taught.
PROTECTED = (
    # the pipeline, the gates and the context pack are the lesson
    "pipeline/",
    ".github/",
    ".devcontainer/",
    "ci/",
    "AGENTS.md",
    "CLAUDE.md",
    "START-HERE.md",
    # the application core is ours — no table's feature is on its critical path
    "backend/app/ingest/",
    "backend/app/retrieve/",
    "backend/app/generate/",
    "backend/app/core/",
    "backend/tests/regression/",
    # shared frontend shell
    "frontend/app/layout.tsx",
    "frontend/app/globals.css",
)

# What each table owns. Anything outside this, on a table branch, is scope creep.
TABLE_PATHS = {
    "1": ("backend/app/features/citations.py",
          "backend/tests/features/test_citations.py",
          "frontend/components/features/Citations.tsx"),
    "2": ("backend/app/features/history.py",
          "backend/tests/features/test_history.py",
          "frontend/components/features/History.tsx"),
    "3": ("backend/app/features/guardrail.py",
          "backend/tests/features/test_guardrail.py",
          "frontend/components/features/Guardrail.tsx"),
    "4": ("backend/app/features/feedback.py",
          "backend/tests/features/test_feedback.py",
          "frontend/components/features/Feedback.tsx"),
    "5": ("backend/app/features/audit.py",
          "backend/tests/features/test_audit.py",
          "frontend/components/features/AuditExport.tsx"),
}

# Written during the lab, never protected — this is the Linear replacement.
ALWAYS_ALLOWED = ("tickets/", "docs/features/")


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=False).stdout


def current_branch() -> str:
    for env in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        import os

        if value := os.getenv(env):
            return value
    return run("git", "rev-parse", "--abbrev-ref", "HEAD").strip()


def changed_files(branch: str) -> list[str]:
    """Files this branch changes relative to main."""
    if branch in ("main", "HEAD"):
        return []
    run("git", "fetch", "origin", "main", "--depth=50")
    base = run("git", "merge-base", "origin/main", "HEAD").strip() or "origin/main"
    diff = run("git", "diff", "--name-only", f"{base}...HEAD")
    return [line for line in diff.splitlines() if line.strip()]


def table_number(branch: str) -> str | None:
    match = re.search(r"table-(\d)", branch)
    return match.group(1) if match else None


def main() -> int:
    branch = current_branch()
    files = changed_files(branch)

    if not files:
        print(f"scope check: nothing to check on '{branch}'")
        return 0

    print(f"scope check: {len(files)} changed file(s) on '{branch}'\n")

    violations: list[tuple[str, str]] = []

    for path in files:
        if path.startswith(ALWAYS_ALLOWED):
            continue

        if path.startswith(PROTECTED) or path in PROTECTED:
            violations.append((path, "PROTECTED — this path may not be changed during the lab"))
            continue

        if table := table_number(branch):
            if not path.startswith(TABLE_PATHS[table]):
                violations.append(
                    (path, f"outside Table {table}'s allowed paths — this is scope creep")
                )

    if not violations:
        print("scope check: PASS — every change is inside the allowed paths")
        return 0

    print("=" * 72)
    print("SCOPE CHECK REFUSED THE BUILD")
    print("=" * 72)
    for path, reason in violations:
        print(f"  {path}\n      {reason}\n")

    if table := table_number(branch):
        print(f"Table {table} may change:")
        for allowed in TABLE_PATHS[table]:
            print(f"  {allowed}")
        print("  tickets/**  docs/features/**")

    print(
        "\nNothing merges and nothing deploys until the diff is inside these paths.\n"
        "If the change is genuinely needed, that is a conversation with the release\n"
        "manager — not something the agent decides on its own."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
