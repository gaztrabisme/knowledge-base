#!/usr/bin/env python3
"""Standalone enrichment script for running on a remote machine with llama-server."""

import json
import sys
from pathlib import Path

from openai import OpenAI

CONTEXT_PROMPT = """<document>
{parent_text}
</document>

Here is the chunk we want to situate within the above section:
<chunk>
{child_text}
</chunk>

Give a short (1-2 sentence) context that explains where this chunk fits in the document and resolves any ambiguous references. Do not repeat the chunk content. Start with the book and topic context."""

LLM_BASE_URL = "http://localhost:8081/v1"
LLM_MODEL = "local-model"


def main():
    work_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    chunks_dir = work_dir / "chunks"

    if len(sys.argv) > 2:
        global LLM_BASE_URL
        LLM_BASE_URL = sys.argv[2]

    client = OpenAI(base_url=LLM_BASE_URL, api_key="not-needed")

    # Verify server is reachable
    try:
        client.models.list()
        print(f"Connected to LLM at {LLM_BASE_URL}")
    except Exception as e:
        print(f"Cannot connect to LLM at {LLM_BASE_URL}: {e}")
        sys.exit(1)

    chunk_files = sorted(chunks_dir.glob("*.json"))
    total_enriched = 0

    for chunk_file in chunk_files:
        slug = chunk_file.stem
        print(f"Enriching: {slug}")

        with open(chunk_file) as f:
            data = json.load(f)

        parent_map = {p["parent_id"]: p["text"] for p in data["parents"]}
        enriched = 0
        skipped = 0

        for child in data["children"]:
            if child.get("context_text"):
                skipped += 1
                continue

            parent_text = parent_map.get(child["parent_id"], "")
            prompt = CONTEXT_PROMPT.format(parent_text=parent_text, child_text=child["text"])

            try:
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                    temperature=0.7,
                    top_p=0.8,
                )
                content = response.choices[0].message.content
                child["context_text"] = content.strip() if content else ""
            except Exception as e:
                meta = child.get("metadata", {})
                book = meta.get("book_title", "")
                section = meta.get("heading_path", "")
                child["context_text"] = f"From {book}, {section}."
                print(f"  LLM error: {e}")

            enriched += 1
            if enriched % 50 == 0:
                print(f"  {enriched} enriched...")
                with open(chunk_file, "w") as f:
                    json.dump(data, f, indent=2)

        with open(chunk_file, "w") as f:
            json.dump(data, f, indent=2)

        total_enriched += enriched
        print(f"  → {enriched} enriched, {skipped} skipped")

    print(f"\nDone. {total_enriched} total chunks enriched.")


if __name__ == "__main__":
    main()
