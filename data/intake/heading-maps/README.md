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
  "back_matter_anchor": "first words of the line where back matter begins",
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

An object-form map with `replace_existing: true` also defines the book's content
start. Ingest skips the heading-based front-matter cut, applies the map after
heading recovery, then removes everything before the first mapped heading. If a
book-title H1 precedes that heading, it is retained; when no title H1 is present,
ingest adds one from the book title when available. For the first map entry,
obvious contents rows followed by a printed page number are skipped so a title
listed in the contents does not become the content start. The existing trailing
index and back-matter cut still runs on the retained content. Books without a map
and books using the list form keep the previous heading-based front-matter cut.

Object-form maps may also set `back_matter_anchor` to the first words of the line
where the back-of-book index begins, or where other back matter listed after the
last chapter or appendix in the printed contents begins. After applying the map
and trimming to its first heading, ingest searches after the map's last heading
for a line beginning with that anchor (case-insensitive, with whitespace and
punctuation normalized) and removes that line through the end of the file. This
lets a map keep appendices while dropping only the subsequent index, notes, or
bibliography. If the anchor is missing, ingest reports it and preserves the
remaining text. Maps without this field keep their existing behavior; the field
is not used with list-form maps.

Each `anchor` is matched case-insensitively after normalizing whitespace and punctuation. The ingest step inserts the heading immediately before the first later non-heading body line whose normalized text starts with the anchor. Entries are applied in order. A title whose anchor is not found is reported as unmatched; the ingest step does not guess a location. Map application adds heading lines only and leaves the body lines unchanged.
