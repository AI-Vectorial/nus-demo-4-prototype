"""python -m app.ingest [--force]"""

from __future__ import annotations

import argparse
import logging
import time

from app.generate import embed
from app.ingest import ingest
from app.retrieve import get_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.ingest", description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="drop and recreate the collection, then re-embed every passage",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    started = time.monotonic()
    count = ingest(get_vector_store(), embed, force=args.force)
    print(f"{count} passages indexed in {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    main()
