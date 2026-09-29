# Heading maps

A heading map is an optional JSON file named for the output Markdown stem, for example `book-slug.json`. Put it in this directory. Its top-level value is an ordered list of entries:

```json
[
  {"title": "Section title", "level": 2, "anchor": "first words of the body line where the section starts"}
]
```

For books whose recovered headings are unreliable, use the object form to make
the map authoritative over headings already present in the Markdown:

```json
{
  "replace_existing": true,
  "entries": [
    {"title": "Section title", "level": 2, "anchor": "first words of the body line where the section starts"}
  ]
}
```

With `replace_existing: true`, existing ATX heading lines outside fenced code
blocks become plain text before mapped headings are inserted. The first H1 is
kept as the book title when the map has no level-1 entry; otherwise all existing
headings are demoted. The list form keeps its existing behavior and leaves
headings already in the Markdown alone.

Each `anchor` is matched case-insensitively after normalizing whitespace and punctuation. The ingest step inserts the heading immediately before the first later non-heading body line whose normalized text starts with the anchor. Entries are applied in order. A title whose anchor is not found is reported as unmatched; the ingest step does not guess a location. Map application adds heading lines only and leaves the body lines unchanged.
