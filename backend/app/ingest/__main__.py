"""python -m app.ingest [--force]"""

from __future__ import annotations

import argparse

from app.generate import embed
from app.ingest import ingest
from app.retrieve import get_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Index the policy corpus.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="recreate the collection and re-embed everything",
    )
    args = parser.parse_args()

    result = ingest(get_vector_store(), embed, force=args.force)
    print(
        f"ingest: {result.documents} documents, "
        f"{result.passages} passages, {result.indexed} indexed"
    )


if __name__ == "__main__":
    main()
