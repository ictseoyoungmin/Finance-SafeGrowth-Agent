import argparse
import sys

from app.integrations.supabase_client import get_supabase_client
from app.rag.embedding_provider import get_embedding_provider
from app.repositories.regulation_versions_repo import FALLBACK_REGULATION_CHUNKS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=64)
    args = parser.parse_args(argv)

    provider = get_embedding_provider()
    supabase = get_supabase_client()
    if supabase.is_configured:
        rows = supabase.select_many("regulation_chunks", filters={}, order="id.asc", limit=args.batch)
        pending = [row for row in rows if row.get("embedding") is None]
        embeddings = provider.embed_batch([str(row.get("chunk_text") or "") for row in pending])
        for row, embedding in zip(pending, embeddings):
            supabase.patch("regulation_chunks", {"id": row["id"]}, {"embedding": embedding})
        print(f"backfilled {len(pending)} supabase chunks")
        return 0

    pending = [chunk for chunk in FALLBACK_REGULATION_CHUNKS if chunk.get("embedding") is None][: args.batch]
    embeddings = provider.embed_batch([str(chunk.get("chunk_text") or "") for chunk in pending])
    for chunk, embedding in zip(pending, embeddings):
        chunk["embedding"] = embedding
    print(f"backfilled {len(pending)} fallback chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
