from __future__ import annotations

import argparse

from app.ingest.ingester import ingest_default_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Index the Aldermere policy corpus")
    parser.add_argument("--force", action="store_true", help="recreate and re-embed the collection")
    arguments = parser.parse_args()
    count = ingest_default_corpus(force=arguments.force)
    print(f"indexed {count} passages")


if __name__ == "__main__":
    main()
