"""`python -m app.ingest [--force]` -- REQ-I1 and REQ-I5.

A command, not a startup hook: re-indexing on document change is out of scope
(PRD section 11), and an import that silently embedded the corpus would make
every test and every boot pay for it.
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.core.config import settings
from app.ingest.loader import CorpusError
from app.ingest.pipeline import ingest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.ingest",
        description="Index the Aldermere policy corpus into the vector store.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="recreate the collection and re-embed everything (REQ-I5)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        result = ingest(force=args.force)
    except CorpusError as error:
        # The corpus is protected and the manifest is the authority, so this is
        # a human's problem to fix, not something to index around.
        print(f"corpus validation failed -- {error}", file=sys.stderr)
        return 1

    print(
        f"indexed {result['passages']} passages from {result['documents']} documents "
        f"into {settings.qdrant_collection} "
        f"({result['skipped']} already present, unchanged)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
