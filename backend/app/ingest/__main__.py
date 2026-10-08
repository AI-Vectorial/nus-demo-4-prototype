"""python -m app.ingest [--force]

Indexes backend/corpus/ into the vector store. Safe to run again: the same
corpus gives the same passages with the same ids. --force drops the collection
first and re-embeds everything, which is what a change of D0 or D1 needs.
"""

from __future__ import annotations

import argparse
import logging

from app.core.config import require, settings
from app.generate import embed
from app.ingest.ingest import ingest
from app.retrieve import get_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.ingest")
    parser.add_argument("--force", action="store_true",
                        help="recreate the collection and re-embed everything")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    report = ingest(
        get_vector_store(),
        embed,
        corpus_dir=settings.corpus_dir,
        max_tokens=require(settings.chunk_max_tokens, "CHUNK_MAX_TOKENS"),
        overlap_tokens=require(settings.chunk_overlap_tokens, "CHUNK_OVERLAP_TOKENS"),
        batch_size=settings.embedding_batch_size,
        force=args.force,
    )
    print(f"{report.documents} documents, {report.passages} passages, "
          f"{report.requests} embedding requests, "
          f"{get_vector_store().count()} passages in the store")


if __name__ == "__main__":
    main()
