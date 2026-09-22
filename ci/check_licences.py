#!/usr/bin/env python3
"""Licence check - provenance and IP.  [M04.4 five-pass review, pass 4]

Fails the build when a dependency carries a licence the repository does not
permit.  The five-pass review asks "where did this come from and may we ship
it"; this is the half of that question a machine can answer.

Pass 4 remains a practitioner flag, not a legal ruling.  A refusal here means
escalate, not "the code is wrong".
"""
from __future__ import annotations

import json
import subprocess
import sys

FORBIDDEN = ("GPL", "AGPL", "SSPL", "CC-BY-SA", "EUPL")
ALLOWED_ANYWAY = {"pip-licenses"}   # tooling, never shipped


def main() -> int:
    raw = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json", "--with-urls"],
        capture_output=True, text=True, check=False,
    ).stdout
    try:
        packages = json.loads(raw or "[]")
    except json.JSONDecodeError:
        print("licence check: could not read the dependency list")
        return 1

    bad = [
        p for p in packages
        if p["Name"] not in ALLOWED_ANYWAY
        and any(token in (p.get("License") or "") for token in FORBIDDEN)
    ]

    if not bad:
        print(f"licence check: PASS - {len(packages)} dependencies, all permissive")
        return 0

    print("=" * 72)
    print("LICENCE CHECK REFUSED THE BUILD")
    print("=" * 72)
    for p in bad:
        print(f"  {p['Name']} {p['Version']}\n      {p['License']}\n      {p.get('URL','')}\n")
    print(
        "A copyleft dependency reached the build.  Escalate to legal and\n"
        "compliance - this is a flag, not a ruling.  Do not relax this check\n"
        "to get a merge through."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
