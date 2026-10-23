"""`python -m app.ingest` -- index the corpus into this table's Qdrant collection."""

from __future__ import annotations

import argparse
import logging

from app.generate import embed
from app.ingest import index_corpus
from app.retrieve import get_vector_store


def main() -> int:
    parser = argparse.ArgumentParser(description="Index the policy corpus.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="recreate the collection and re-embed everything (REQ-I5)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    store = get_vector_store()
    if args.force:
        store.reset()
    written = index_corpus(store, embed)
    print(f"indexed {written} passages; collection now holds {store.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
