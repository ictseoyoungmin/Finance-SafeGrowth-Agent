import argparse
import sys

from app.ingestion.connectors.fss_rss import FssRssConnector
from app.repositories.regulation_sources_repo import get_regulation_sources_repository
from app.services.regulation_ingestion_service import get_regulation_ingestion_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all")
    parser.add_argument("--fetch-full-text", action="store_true")
    args = parser.parse_args(argv)

    sources_repository = get_regulation_sources_repository()
    ingestion_service = get_regulation_ingestion_service()
    connector = FssRssConnector(
        sources_repository=sources_repository,
        ingestion_service=ingestion_service,
        fetch_full_text=args.fetch_full_text,
    )

    sources = sources_repository.list_active()
    if args.source != "all":
        sources = [source for source in sources if source.id == args.source]

    for source in sources:
        if source.source_type != "rss":
            print(f"skip {source.id} {source.source_type}")
            continue
        items = connector.poll(source)
        print(f"polled {source.id}: {len(items)} rss items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
