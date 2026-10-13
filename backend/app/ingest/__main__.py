"""Index the policy corpus: `python -m app.ingest [--force]`.

REQ-I1: indexes the whole corpus from empty. REQ-I4: running it again changes
nothing, because every passage id is derived from its document, version,
section and text -- so a second run overwrites each passage with itself.
REQ-I5: --force drops the collection first and re-embeds everything, which is
what a changed embedding model or a removed section needs.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.ingest.chunk import chunk_document, load_corpus
from app.retrieve.store import Passage, VectorStore

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"


@dataclass(frozen=True)
class IngestResult:
    documents: int
    indexed: int
    seconds: float


def ingest(
    corpus_dir: Path,
    *,
    store: VectorStore,
    embed: Callable[[list[str]], list[list[float]]],
    max_tokens: int,
    overlap_tokens: int,
    force: bool = False,
) -> IngestResult:
    started = time.monotonic()
    documents = load_corpus(corpus_dir)
    chunks = [
        chunk
        for document in documents
        for chunk in chunk_document(document, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    ]

    if force:
        store.recreate()
    else:
        store.ensure_ready()

    # One call; the provider client batches it by EMBEDDING_BATCH_SIZE (REQ-I6).
    vectors = embed([chunk.embedding_text for chunk in chunks])
    store.upsert([
        Passage(
            id=chunk.id,
            text=chunk.text,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            section=chunk.section,
            embedding=vector,
            metadata=chunk.metadata,
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ])
    return IngestResult(len(documents), len(chunks), time.monotonic() - started)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.ingest", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--force", action="store_true",
                        help="drop the collection and re-embed everything")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    from app.core.config import settings
    from app.generate import embed
    from app.retrieve import get_vector_store

    args = parse_args(argv)
    store = get_vector_store()
    result = ingest(
        CORPUS_DIR,
        store=store,
        embed=embed,
        max_tokens=settings.chunk_max_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
        force=args.force,
    )
    print(
        f"indexed {result.indexed} passages from {result.documents} documents "
        f"in {result.seconds:.1f}s -- collection now holds {store.count()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
