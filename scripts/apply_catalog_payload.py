#!/usr/bin/env python3
"""Add catalog domains and tags to Qdrant points and index the filter fields."""

import os
from urllib.request import Request, urlopen

from qdrant_client import models

from knowledge_base.books import book_domain, load_catalog
from knowledge_base.config import COLLECTION_NAME
from knowledge_base.search import get_client


def _require_qdrant_server() -> str:
    base_url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    request = Request(f"{base_url}/collections", method="GET")
    try:
        with urlopen(request, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"Qdrant health check returned HTTP {response.status}")
    except Exception as exc:
        raise SystemExit(
            f"Refusing to run: Qdrant server did not answer GET {base_url}/collections: {exc}"
        ) from exc
    return base_url


def main() -> None:
    base_url = _require_qdrant_server()
    client = get_client()
    catalog = load_catalog()

    schema = client.get_collection(COLLECTION_NAME).payload_schema
    created = []
    if "book" not in schema:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="book",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        created.append("book")

    for slug, entry in catalog.items():
        client.set_payload(
            collection_name=COLLECTION_NAME,
            payload={
                "domain": entry.get("domain") or book_domain(slug),
                "tags": entry.get("tags") or [],
            },
            points=models.Filter(must=[models.FieldCondition(
                key="book", match=models.MatchValue(value=slug),
            )]),
        )

    schema = client.get_collection(COLLECTION_NAME).payload_schema
    for field in ("domain", "tags"):
        if field not in schema:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            created.append(field)

    print(f"Applied domain and tags payload to {len(catalog)} catalog books.")
    print(f"Qdrant server: {base_url}")
    print("Created keyword payload indexes: " + (", ".join(created) if created else "none (already present)"))


if __name__ == "__main__":
    main()
