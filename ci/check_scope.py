"""Did this change touch something it may not?

M04.3's permission boundary, made mechanical. An agent that has been told no by a
human, and reaches for a protected file anyway, is stopped here -- checkable, not
narrated.

WHAT IS PROTECTED, AND WHY

Each table owns their whole application. app/, tests/, frontend/ and tickets/ are
theirs to change however they like -- that is the point of the lab.

What is protected is the specification and the process: the documents that define
what is being built, the pipeline that governs how, the checks themselves, and the
corpus every table answers from.

The corpus is the interesting one. A table whose retrieval underperforms will be
tempted to edit a policy document to contain the words they searched for. That makes
the demo work and the product worthless -- and it destroys the comparison between
five tables, which only holds if all five answer from the same documents.

Exit 0 to allow, 1 to refuse.
"""

from __future__ import annotations

import os
import subprocess
import sys

# Nobody edits these on any branch, for any reason.
PROTECTED = (
    "pipeline/",
    ".github/",
    "ci/",
    "AGENTS.md",
    "CLAUDE.md",
    "START-HERE.md",
    "docs/PRD.md",
    "docs/features.md",
    "docs/project-brief.md",
    "backend/corpus/",
    "scripts/",
)

# What a table may freely change.
OWNED = (
    "backend/app/",
    "backend/tests/",
    "backend/requirements.txt",
    "backend/requirements-dev.txt",
    "frontend/",
    "tickets/",
    "docs/design/",
    "README.md",
)


def changed_files() -> list[str]:
    """Files this change touches, compared against the branch it targets."""
    base = os.environ.get("GITHUB_BASE_REF")
    if base:
        target = f"origin/{base}"
        subprocess.run(
            ["git", "fetch", "origin", base, "--depth=50", "--quiet"], check=False
        )
    else:
        target = "origin/main"
        subprocess.run(
            ["git", "fetch", "origin", "main", "--depth=50", "--quiet"], check=False
        )

    for rev in (f"{target}...HEAD", "HEAD~1"):
        result = subprocess.run(
            ["git", "diff", "--name-only", rev],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return [f for f in result.stdout.splitlines() if f.strip()]
    return []


def refuse(violations: list[tuple[str, str]]) -> None:
    line = "=" * 72
    print(line)
    print("SCOPE CHECK REFUSED THE BUILD")
    print(line)
    print()
    for path, rule in violations:
        print(f"  {path}")
        print(f"      {rule}")
        print()
    print("These files define what is being built and how it is governed.")
    print("They are not yours to change, and no amount of green tests makes")
    print("a diff that touches them mergeable.")
    print()
    print("If you believe one genuinely has to change, stop and ask a human.")
    print("Do not edit it and explain afterwards.")
    print()
    print(line)


def main() -> int:
    files = changed_files()

    if not files:
        print("scope check: nothing to check")
        return 0

    violations = [
        (path, f"protected: {prefix}")
        for path in files
        for prefix in PROTECTED
        if path == prefix.rstrip("/") or path.startswith(prefix)
    ]

    if violations:
        refuse(violations)
        return 1

    print(f"scope check: PASS - {len(files)} file(s), none protected")
    for path in files[:20]:
        owned = any(path.startswith(o.rstrip("/")) for o in OWNED)
        print(f"  {'ok ' if owned else '?  '} {path}")
    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
