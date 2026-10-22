# R5 — One archive and ingestion skill

Owner: Huy. Run: kbu-2026-10-07. Inspection date: 2026-10-10.

**Recommendation:** use one `archive-and-ingest` skill, one common manifest, and source adapters for Domestika, Coursera, books, papers, and code repositories. An adapter translates a source's structure and access method into the common inventory. The core preserves files, builds reading material, checks results, and prepares the knowledge base (KB) handoff. Ingestion means turning preserved material into searchable records. Archiving and indexing have separate completion states: neither a ZIP archive (a container holding packaged files) nor a finished downloader proves the material is searchable.

Formats used below: PDF means Portable Document Format; EPUB is a packaged electronic publication; HTML is Hypertext Markup Language, used for web-page content. MP4 is a video-file container. VTT means Web Video Text Tracks, a timed-caption format. HLS means HTTP Live Streaming, the playlist-and-segment media format used by the existing Domestika packager. JSON means JavaScript Object Notation, a structured data format; JSONL holds one JSON record per line. A content hash, such as SHA-256, is a fingerprint used to compare file contents. A blob is a stored block of file bytes. These names describe the formats handled by the inspected tools. [D2, K1]

This is a design report, not an implementation or a completed source archive. All proposed functions, schemas, update behavior, and acceptance cases below are proposals. Statements headed “Observed” describe inspected code or the owner's supplied observations. “Inference” identifies conclusions drawn from that evidence. Report verification is recorded in the Output sample section.

The inspection covered the complete Domestika `SKILL.md`, all 3 Markdown references, and all 5 script source files, including the JSON rules file. Compiled Python cache files are not source tools. The KB pipeline runner, ingestion module, chunker, indexer, embedding helper, configuration, and the pipeline sections of `CLAUDE.md` were read. Litgraph's arXiv and seed ingestion modules, command dispatch, document schema, and relevant project guidance were read. No course browser session, ingestion command, model, GPU, container, or existing service was used. Writes are confined to this R5 folder.

## Shared core vs adapters

The common core should own the following stages. A **probe** is a small check before a full transfer. A **reading copy** is a faithful, traceable English document derived from source text and selected still images. **Provenance** is the information needed to locate the exact source of a passage or figure.

| Stage | Shared responsibility | Source-specific input or check |
|---|---|---|
| Discover | Resolve identity; inventory ordered containers and items; establish the requested scope; record expected membership and access states. | Course tree, book contents, paper identifiers, or repository file tree. |
| Collect | Save permitted metadata and sanitized page content; retain inaccessible items as explicit gaps. Do not begin bulk media transfer. | Signed-in page parser, platform application programming interface (API), local book parser, scholarly feed, or repository API. |
| Probe | Confirm access, formats, language choices, protection state, representative readability/playability, and transfer requirements. Every selected item gets a capability check. | HLS playlists, progressive video headers/streams, PDF text layer, EPUB resources, paper body availability, or complete repository tree. |
| Package | Fetch permitted assets into staging; normalize names; hash files; render portable documents; assemble the selected archive. | A transport description and normalized content, rather than platform-specific ZIP logic. |
| Verify | Compare exact expected and actual members; check hashes, media streams, timed captions, document anchors, rendered pages, and ZIP integrity. | Additional source-specific checks and authoritative inventory evidence. |
| Reading copy | Preserve original text; build an optional English derivative; retain source spans, image links, transformations, and removal logs. | Native caption language, source section boundaries, and adapter-specific exclusion rules. Return `not_applicable` when no derivative is requested. |
| Hand off | Emit sanitized text and image records plus privacy and provenance; record acknowledgement from the KB consumer. | Source locators and permissions; adapters do not write directly to an index. |

Use a small function interface, not a new downloader framework for each source. Inputs and results are data objects validated against the common schema. `Context` contains an allowed output root, selected item identifiers, language/quality requirements, tool configuration, cancellation state, and an ephemeral reference to authorized browser access when needed. An ephemeral reference is a handle that exists only during the collection session; it is not a cookie export. The core invokes these functions in order:

| Proposed function | Input | Output and boundary |
|---|---|---|
| `capabilities()` | Adapter identifier and version. | Supported source/item kinds, transports, language evidence, reading-copy modes, and checks. Unknown capability is explicit. |
| `discover(locator, context)` | User-selected course, book file, paper identifier/query, or repository and revision. | `SourceIdentity`, ordered `ItemStub` records, inventory evidence, selection, and discovery completeness. Never infer access from a different purchased item. |
| `collect(identity, inventory, context)` | Discovered selected items and authorized access handle. | Common `Item` and `AssetSpec` records, sanitized text blocks, gaps, and private transport references. Preserve item identity and ordering. |
| `probe(items, requirements, context)` | Selected assets, language/quality requirements, and private references. | Per-asset `ProbeResult`: access, protection, available/selected tracks, format, exact duration/bytes when known, and reason for any failure. |
| `resolve_transport(asset_id, context)` | Asset identifier already collected and authorized. | Temporary fetch descriptor: `local_copy`, `http_file`, `hls`, or `repository_blob`; an adapter refreshes an expired signed URL through the same authorized source. |
| `normalize(collected, verified_assets, context)` | Collected text and completed local asset receipts. | Ordered `ContentBlock` records with source spans, native language evidence, headings, figure candidates, and adapter policy identifiers. |
| `source_checks(manifest, receipts, context)` | Manifest and local results. | Additional assertions and a list of exact gaps. Common verification still runs. |

The core functions are `fetch_asset`, `package`, `verify`, `build_reading_copy`, and `emit_kb_handoff`; they consume these same records for every adapter. A **receipt** records what was actually fetched or generated, including its file path, byte count, content hash, and verification result. Common transports perform downloads; adapters resolve access and interpret source structure. A direct MP4 therefore does not need an HLS-specific downloader. HTTP Live Streaming (HLS) splits media into segments described by playlists; MP4 is a video file container, and Web Video Text Tracks (VTT) is the timed-caption format used here.

Keep one skill entry point and one archive command, with a registry selecting `adapters/domestika`, `adapters/coursera`, `adapters/books`, `adapters/papers`, or `adapters/repos`. A future platform adds a registry entry, adapter, normalization rules, and contract fixtures; it does not add another skill, ZIP builder, figure pipeline, or KB importer. Preserve Domestika's existing collector as its adapter-specific browser helper. Shared script modules own manifest validation, transports, rendering, reading-copy mechanics, and handoff. Transport allowlists remain adapter data rather than a universal rule that permits arbitrary hosts.

Observed: `reading_copy.py` imports Domestika's manifest validator, filename functions, and caption helpers; its lesson metadata uses `course_id`, unit number, and lesson number. `package_domestika.py` embeds the permitted media hostname, HLS selector, browser path, renderer, and archive logic. These are the concrete coupling points to separate, not grounds for rewriting working frame selection and verification. [D2]

Inference: extraction should first preserve the existing Domestika behavior behind the interface; Coursera should provide the second course implementation that demonstrates the transport seam. Books, papers, and repositories demonstrate why the common hierarchy must use generic containers/items rather than require “units” and “lessons.” All artifacts belong to the same pipeline, but MP4/audio files are archive assets only. Only text and still images reach embedding jobs. An **embedding** is a numeric representation used to retrieve related content; a multimodal model can represent images as well as text.

## Adapters

### Domestika

Observed: the collector runs in the user's signed-in course unit page, discovers same-origin unit links (links sharing the page's protocol, hostname, and port), fetches them with the browser session, reads `__INITIAL_PROPS__`, and verifies course/unit/lesson totals. It sanitizes page fragments and extracts playback URLs without reading cookies directly. The packager allows HLS on `cdn-videos.domestika.org`, uses `yt-dlp`, merges video/audio into MP4, saves VTT captions, and renders one annotated PDF document per selected unit. The requested caption language and the playlist's `DEFAULT=YES` audio-language caption are both retained, deduplicated when equal. [D1, D2]

The adapter should preserve course ID, unit and lesson IDs, page links, durations, transcript fragments, tasks, resource links, and default-audio evidence. The core produces the existing unit PDFs, MP4/VTT pairs, ZIP, optional English reading-copy PDF, searchable Markdown exports, frame files, and KB handoff. Preserve the native transcript as primary evidence; platform English captions remain a checking source when native captions exist.

Limits: this collector depends on specific page markup; it does not collect a separate final-project page. Attachments are links unless explicitly selected for download. The existing packager is tied to Chrome on macOS. Its video reuse checks do not establish that a source revision is unchanged, and its candidate-frame cache uses video size and modification time rather than a content hash. [D1, D2] The new core should add content-based receipts and configurable rendering. A playlist's default audio tag is evidence of a default, not independent proof of the teacher's spoken language: if language evidence conflicts, record the conflict and block the native-language reading copy rather than invent a language.

### Coursera

Evidence date: **2026-10-07**, supplied by the owner from a signed-in browser. No Coursera access was performed for R5. These are observations about that measured access, not claims about every course or later session. A public evidence URL for the owner's measurement was not supplied.

The adapter maps `/api/onDemandCourseMaterials.v2` modules, lessons, and typed items, including lock states, into the common hierarchy. Lectures use `/api/onDemandLectureVideos.v1`: direct progressive MP4 choices at **720p, 540p, 360p, and 240p**, plus MP3 audio. The observed signed CloudFront URLs work with `curl` without cookies, and the measured media has no encryption. VTT and plain-text TXT captions are available in multiple languages; the exact language count is **not found** because the supplied count was approximate. The adapter must enumerate actual language identifiers before selecting tracks. It must not invent an HLS default-audio language for progressive MP4.

Readings of type `supplement` come as Hypertext Markup Language (HTML) from `/api/onDemandSupplements.v1`. Sanitize and preserve them with their item IDs. Readings of type `ungradedWidget` open in an embedded frame; a reliable authorized collection method is **not found**. Record these as unresolved gaps, with metadata only. Labs, quizzes, and assignments were locked after the measured session ended; preserve their titles/types/lock states, do not attempt access workarounds. Slide attachments on the measured lectures were absent.

Outputs are module PDFs with lecture file/caption markers and readings, MP4/VTT assets, optional selected MP3 assets, a ZIP, a faithful reading copy when native captions can be established, and text/image KB records. Direct-download probing checks the selected file and media streams instead of forcing it through Domestika's HLS format selector. A URL's expiry triggers authorized recollection, not cookie extraction. A complete inventory can coexist with a partial content archive: report locked and unresolved items individually. MP3 and MP4 stay outside embeddings; caption text and approved still frames are eligible.

### Books

Books use local EPUB or PDF files that the user supplies or that already lie within an authorized source directory. EPUB is a packaged electronic publication. Observed: the KB uses MarkItDown conversion for EPUB/HTML, reconstructs PDF headings from PyMuPDF bookmarks with fallback paths, repairs heading structure, strips selected front/back matter, and requires catalog entries in `BOOKS` for its bulk ingestion paths. Existing Markdown output causes ingestion to skip that source. [K1, K2]

The adapter should preserve the original book, bibliographic metadata, edition when available, ordered sections, extracted text, and figure occurrences. A PDF occurrence has a physical page and rectangle; an EPUB occurrence has a package resource path, element identifier when present, and position in the publication's reading order. EPUB's package document declares resources and the spine declares default reading order. [EPUB specification](https://www.w3.org/TR/2026/REC-epub-33-20260113/)

Outputs: original EPUB/PDF, normalized Markdown with a provenance sidecar, figure files with caption/context records, extraction-quality evidence, and KB records. An optional English reading edition is a derivative, not a replacement for the original edition. Do not manufacture physical page numbers for a reflowable EPUB. Scanned pages and garbled text require an explicit extraction failure or optical character recognition (OCR), meaning conversion of visible letter shapes into text. A DRM-protected book remains blocked; this adapter does not remove protection. Bibliographic fields that cannot be established are `null` with reason `not found`.

### Papers

Observed: litgraph's arXiv adapter reads an Atom feed, uses a versionless `arxiv:<id>` document key, fetches rendered arXiv HTML and reduces it with `trafilatura`, then falls back to the abstract. A present document is skipped; database insertion also uses `ON CONFLICT DO NOTHING`. It stores title, authors, publication date, URL, text, and categories, but does not preserve a source PDF or figure records. The `full_text_ok` counter is a text-length check, not proof of a complete paper. [L1, L2]

**OpenAlex ingestion code: not found.** The inspected Python tree has no OpenAlex matches; litgraph's Phase 1 design explicitly defers OpenAlex citation edges. Treat OpenAlex support as a new adapter component rather than existing functionality. [L3] OpenAlex work metadata includes `referenced_works`, `abstract_inverted_index`, and `best_oa_location`; the best open-access location can be absent. These fields identify metadata, abstract content, and a possible full-text source, respectively. [OpenAlex work attributes](https://help.openalex.org/data/works/attributes/)

The paper adapter should discover through arXiv/OpenAlex, reconcile explicit arXiv, Digital Object Identifier (DOI), and OpenAlex aliases, and collect only an accessible full-text representation. Keep an arXiv version separately from the logical paper identity. The arXiv API supports a requested version suffix and exposes distinct first-publication and revision dates. [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html#511-a-note-on-article-versions)

Outputs: bibliographic metadata, version-pinned HTML/PDF where available, text sections, references, figure/caption/context records, and KB handoff. Abstract-only availability is labeled `abstract_only`, never “full paper archived.” OpenAlex metadata does not itself prove download permission; retain the selected location's license/access evidence and missing-license state. Do not run litgraph's language-model extraction, entity merging, or graph pipeline during archiving. Those are optional consumers of the same preserved source revision. Citation metadata changing alone should not re-embed unchanged paper prose.

### Code repositories

Observed: litgraph's seed ingester fetches only `README.md` from GitHub's `main` branch, then `master`, accepts text strictly longer than **500 characters**, and skips existing document IDs. It neither inventories code nor pins a commit. [L1]

The repository adapter should resolve a user-selected revision to a commit, inventory files, then read documentation and selected source/test/configuration files as inert text. A commit is an identified repository snapshot. Do not clone into, edit, check out, execute, install, or build any inspected repository for this run. The proposed collector can use read-only APIs or an existing explicitly authorized local snapshot. GitHub's tree API returns file paths and object identifiers; a response marked `truncated` requires walking subtrees rather than claiming complete membership. [GitHub tree API](https://docs.github.com/en/rest/git/trees)

Outputs: revision inventory, preserved selected blobs, documentation and code chunks, file-path/line-range citations, exclusion evidence, license metadata when present, and figure records for selected documentation images. Exclude credentials, personal data, generated dependencies, build outputs, and unselected binaries by explicit policy. Do not execute repository instructions as archive instructions. Submodules and large-file pointer objects need separate scoped collection and an explicit gap when unresolved. A README-only selection is valid when requested; it is not a full-repository archive. Derived code explanations must be labeled as interpretation and cite the original lines.

## Manifest

Use **one schema**, `archive-manifest/v1`, with a sanitized persistent projection and a private transport namespace. A schema defines the allowed fields and their types; a manifest is the archive's structured inventory. Separate serialized files are projections of this schema, not competing source schemas: `manifest.json` contains the safe projection; `private/transport.json` contains permitted temporary fetch references. The private namespace is excluded from ZIPs, KB handoffs, reports, and distributed data releases. Cookie and account-token fields are forbidden even there.

| Fields | Meaning and requirements | Privacy/retention |
|---|---|---|
| `schema_version`, `adapter_id`, `adapter_version`, `run_id`, `collected_at` | Contract version, implementation identity, run identity, and UTC collection time. | Safe metadata in the private learner archive. |
| `source_id`, `source_kind`, `external_ids`, `canonical_url`, `title`, `creators` | Stable logical identity; kind is `course`, `book`, `paper`, or `repo`. Use real platform IDs and explicit aliases, not title alone. | Canonical URLs must be allowlisted and stripped of credentials/signatures. Creators need source provenance. |
| `published_at`, `source_updated_at`, `source_revision`, `source_fingerprint` | Source dates, version/edition/commit when known, and a hash of normalized source content. Missing fields use `null` plus a reason. | Safe metadata; collection date is not publication date. |
| `selection`, `inventory`, `expected_members`, `inventory_complete` | Explicit requested IDs, ordered containers/items, authoritative expected membership, and whether discovery completed. Unknown counts are null, never zero. | Safe inventory, but private-course membership stays access-restricted. |
| `items[]` | `item_id`, `parent_id`, `order`, `kind`, title, source locator, `access_state`, and reason. States include available, locked, unavailable, unsupported, and unknown. | No account pages, unrelated projects, or raw authorization data. |
| `assets[]` | `asset_id`, `item_id`, role, relative path, media type, bytes, SHA-256 hash, duration, dimensions, available/selected languages, default-audio evidence, `transport_ref`, and protection state. | File/probe metadata is retainable; `transport_ref` is opaque and unresolved in exports. DRM means Digital Rights Management, the protection systems this design does not bypass. |
| `content_blocks[]`, `figures[]`, `derivations[]` | Text spans and figure occurrences; links to originals; transform/tool versions; native-language evidence; translation/audit status; removed-content rule IDs. | Source content remains restricted as required; generated descriptions are labeled as derived. |
| `rights`, `privacy` | Permission basis, license when known, owner access scope, audience, export/distribution controls, and personal-data status. | Unknown license is not permission to publish. Personal data defaults to quarantine, not searchable export. |
| `verification`, `gaps`, `archive_state`, `kb_state` | Exact check results and artifact hashes; item-specific failures; independent archive and KB status. | Export only sanitized summaries. Pending handoff is not completed ingestion. |
| `private.transport[]` | `transport_ref`, temporary signed playback/download URL, expiry when known, source host, and refresh evidence. | Capability-bearing URLs stay in restricted local working storage only, outside shared bundles; expiry dates can also remain private. Delete when resume is no longer needed. |
| Forbidden fields | Cookies, browser cookie stores, account/access tokens, authorization headers, user credentials, and unrestricted raw API/player dumps. | Never collect, persist, embed, or report them. Use existing session access without exporting its credentials. |

“Safe” means safe to retain with the permitted archive, not safe to publish copyrighted course/book text. Preserve licensed/public versus private data scopes through every derivative. A signed media URL is a private temporary playback capability already exposed to the authorized user; it is not a public citation or content identifier. Hashes must derive from bytes or normalized content, not the signed URL. Hash a stable sanitized representation that excludes collection timestamps, URL expiry/signature changes, and temporary file paths.

Observed: the Domestika collector removes scripts and attributes but retains permitted HTTP(S) `href` and `src` values, including their query strings. Its PDF renderer also preserves such links. [D2] Inference: merely deleting `media_url` is insufficient redaction. The new export validator must inspect all URLs in HTML, captions, attachments, PDFs, logs, and metadata. Use source-specific allowlists for public citation URLs and localize preserved images; unknown signed/query-bearing links become private references or explicit omissions. Render normalized content without fetching uncollected remote images.

## Image extraction

Extract **figure occurrences**, not just unique image files. An occurrence ties an image to the particular page or lesson where it is discussed. Shared image bytes can be stored once, but each occurrence keeps its own caption, surrounding text, and provenance. This matters when the same illustration returns in a later comparison.

For PDFs, use PyMuPDF to enumerate displayed images with `Page.get_image_info(xrefs=True)` and obtain occurrence rectangles with `Page.get_image_rects()`. An `xref` is a PDF object's internal reference number; an inline image may lack one. Read text blocks with their coordinates before cleanup loses page structure. PyMuPDF documents these APIs and unrotated-page coordinates. [PyMuPDF Page API](https://pymupdf.readthedocs.io/en/latest/page.html)

When an ordinary raster image can be extracted, use `Document.extract_image(xref)` and account for its transparency mask. A raster image is a pixel grid. When the figure is vector artwork, a composite of images/text, inline content, or a scanned-page region, render the detected rectangle rather than saving only one underlying image object. PyMuPDF's image recipes document extraction, masks, and clipped rendering. [PyMuPDF image recipes](https://pymupdf.readthedocs.io/en/latest/recipes-images.html) Vector drawings are shapes and paths; proposed detection groups their nearby bounds and presents uncertain regions for review. `get_drawings()`/`cluster_drawings()` and `get_pixmap(clip=...)` provide the corresponding page facilities. [PyMuPDF Page API](https://pymupdf.readthedocs.io/en/latest/page.html)

Use `pdfplumber` as an optional layout cross-check for word bounding boxes, image positions, and crops. Its documentation explicitly says it does not directly reconstruct image content, so it should not be designated the image-byte extractor. [pdfplumber documentation](https://github.com/jsvine/pdfplumber/blob/stable/README.md) The proposed caption linker searches nearby text for source labels such as “Figure” or “Fig.”, checks column/layout proximity, and follows explicit references in nearby paragraphs. This is a heuristic, not a guaranteed caption detector. Retain all candidate links and their boxes; ambiguous or missing captions get status `ambiguous` or `not_found`. Do not invent a caption to fill a required field. A generated description, if requested, is stored separately as derived text.

A PDF figure record must carry source asset hash, 1-based physical page, printed page label when available, unrotated rectangle in PDF points, page size, rotation/crop metadata, original caption text with its own rectangle/span, preceding/following paragraph spans, and heading path. Use page/rectangle provenance even when the logical caption is absent. Preserve OCR text separately with extraction method and review status; the original pixels remain the evidence. PyMuPDF's OCR facility uses Tesseract, and its guidance recommends computing OCR once per page and reusing the result. [PyMuPDF OCR guidance](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html) No OCR or bulk rendering was run in R5.

For reading copies, use the existing frame files and semantic figure blocks as the primary source. Observed: `reading_copy.py` retains extraction times in `frames.json`, puts timestamped `On screen:` and `Shows:` captions in lesson Markdown, renders figure/source appendices, and can export both Markdown figures and a section-to-PDF-page index. [D2, D3] Add a generated `figure-map.json` sidecar containing `figure_id`, original video hash, lesson ID, requested seconds, actual selected frame presentation timestamp when measured, frame hash, transcript cue IDs, section time range, caption text, reading-copy PDF hash, and rendered page/rectangle. The current section-page index does not itself establish each figure's page; derive the figure mapping after PDF rendering and fail a missing figure anchor.

Reuse full-resolution frames instead of extracting a recompressed image from the reading-copy PDF. If only the PDF remains, extract its images and join printed figure anchors to the sidecar; absent sidecar/video evidence means timestamp provenance is `not found`, not inferred from filename alone. FFmpeg seeking may land initially on a preceding seek point; accurate seeking decodes/discards the preceding interval when transcoding. [FFmpeg documentation](https://www.ffmpeg.org/ffmpeg.html) Therefore a requested extraction time is not a claim of measured frame accuracy. Retain requested time and actual frame time separately.

Embed selected still-image pixels with the future multimodal encoder; also give the KB original caption, on-screen text, and nearby prose as separately attributed text. Deduplicate exact pixel content within the same permitted privacy scope. Keep separate occurrences and do not merge translations or contexts merely because their picture is identical. Every image must be viewable with its source context. Text-only search must still find its caption. Neither audio nor video files are passed to a model for embedding.

## Handoff to the knowledge base

Observed current behavior: `scripts/ingest_all.py` calls ingest, chunk, optional enrich, and index. The configured text embedding model is `jinaai/jina-embeddings-v5-text-small-retrieval`; indexing stores a dense vector plus a BM25 keyword vector. A dense vector represents semantic similarity; BM25 is keyword ranking. The configured child cap is **250 tokens** and parent cap **1900 tokens**, measured by the `cl100k_base` tokenizer. A token is a unit of encoded text. The current payload contains book/chapter/section headings and text, but no page, timestamp, image, source revision, or privacy fields. [K1, K2]

Further observed limitations: `clean_markdown()` removes Markdown image links. `ingest_all()` and `chunk_all()` skip existing output files. `index_book()` refuses the entire book if any existing point is found. Positional parent/child IDs depend on chunk order. [K2] Consequently, pointing new course PDFs at the present bulk runner will not satisfy figure ingestion or selective re-archiving. Those behaviors must change deliberately; R5 did not change them.

Define a KB ingestion boundary, `consume_archive_handoff(bundle_root, envelope)`. It validates paths, privacy, hashes, membership, and producer/consumer schema versions without loading a model. The producer exports `kb-handoff.json` (envelope), `text-chunks.jsonl`, `image-records.jsonl`, and referenced local image blobs. JSON is JavaScript Object Notation; JSONL is one JSON record per line. A pure, versioned chunking function shared with the KB converts normalized source blocks into the handoff's text chunks; the consumer does not split those chunks again. Video/audio stay in the archive; the handoff lists their stable asset IDs as provenance only. The exact proposed contract is:

| Record | Required fields and semantics |
|---|---|
| Envelope | `schema_version="kb-handoff/v1"`, `source_id`, `source_revision`, `source_kind`, `title`, `canonical_url`, `adapter_version`, `manifest_sha256`, `selection`, `inventory_complete`, `archive_state`, `privacy_scope_id`, `rights`, `privacy`, `text_records_path`, `image_records_path`, exact counts/hashes, `previous_revision`, and `deletion_candidates`. |
| Text chunk delivered to ingester | `record_id`, `logical_block_id`, `source_id`, `item_id`, `asset_id`, `source_revision`, `representation` (original, translation, derived), `language`, `child_id`, `parent_id`, `child_text`, `parent_text`, `context_text`, `content_sha256`, `heading_path`, `image_occurrence_ids`, `provenance`, `derivation`, `quality`, `privacy`, `token_count`, `tokenizer`, `chunker_version`, `embedding_input_sha256`, and `embedding_space_id`. Preserve the existing parent/child arrangement. |
| Image record | `record_id`, `figure_id`, `blob_id`, `source_id`, `item_id`, `source_revision`, relative `image_path`, `image_sha256`, integer `width_pixels`/`height_pixels`, `caption`, `caption_status`, `caption_provenance`, `on_screen_text`, `context_record_ids`, `context_excerpts` with source spans, `occurrences[]`, `extraction`, `quality`, `privacy`. |
| Provenance entry | Common `asset_id`, asset hash, canonical citation URL, and locator type. PDF: page index/label and rectangle; course: container/lesson IDs, cue IDs and seconds; EPUB: package resource and element/span; repository: commit, path, line range; paper: identifier and version plus PDF/HTML locator. |
| Privacy object | `audience`, `privacy_scope_id`, `contains_credentials=false`, `contains_signed_urls=false`, `personal_data_status`, `allow_remote_processing`, `allow_distribution`, and `excluded_reason` when needed. Unknown personal-data status is quarantined; credentials or signed URLs reject the record outright. |

Source records retain paragraph/cue/line spans. The shared chunker creates bounded parent/child chunks within source items and attaches every contributing span after splitting, merging, or overlap. `provenance` contains separate `child_spans`, `parent_spans`, and `context_spans` arrays; each span maps a half-open character interval in its normalized text to the original source locator. Half-open means the start character is included and the end character is excluded. This prevents a child chunk from losing its PDF page or caption cue, and prevents parent context from acquiring an unsupported citation. Reuse the current size caps for compatibility, but reject oversize results and preserve exceptions explicitly. Do not indiscriminately apply book front/back-matter rules to papers, code, or course tasks. Captions from a figure already linked to a lesson are one canonical text representation, not a second competing ingestion of the same rendered PDF.

All identifiers/hashes/paths/text are strings; counts, character offsets, page indexes, and pixel dimensions are integers; times and rectangle coordinates are numbers; privacy switches are booleans; ordered membership/spans are arrays. Unknown optional source facts are null with reasons. Required content hashes, token counts, and provenance must be resolved before intake. Unrecognized schema versions fail closed. Paths must remain relative to the handoff root after resolution, including symbolic links (filesystem paths pointing to another path); a record cannot cause the ingester to fetch a URL or read outside that root.

This is a **record template**, not measured course output. `envelope` represents `kb-handoff.json`; `text_chunk` and `image_record` represent one line in their respective files. Angle-bracket values are placeholders; the token-count and pixel-dimension placeholders must become integers before schema validation. Numeric times/page/rectangles below are illustrative values, not claims about an archived lesson:

```json
{
  "envelope": {
    "schema_version": "kb-handoff/v1",
    "source_id": "course:domestika:<course_id>",
    "source_revision": "<normalized_content_sha256>",
    "source_kind": "course",
    "title": "<course_title>",
    "canonical_url": "<safe_course_page_url>",
    "adapter_version": "<adapter_version>",
    "manifest_sha256": "<sanitized_manifest_sha256>",
    "selection": {"item_ids": ["<lesson_id>"], "mode": "selected_items"},
    "inventory_complete": true,
    "archive_state": "verified_selected_scope",
    "privacy_scope_id": "<owner_scope>",
    "rights": {"basis": "authorized_user_access", "license": null, "license_reason": "not found"},
    "privacy": {"audience": "private", "privacy_scope_id": "<owner_scope>", "contains_credentials": false, "contains_signed_urls": false, "personal_data_status": "reviewed_clear", "allow_remote_processing": false, "allow_distribution": false},
    "text_records_path": "text-chunks.jsonl",
    "image_records_path": "image-records.jsonl",
    "counts": {"text_chunks": 1, "image_records": 1},
    "record_file_hashes": {"text_chunks": "<jsonl_sha256>", "images": "<jsonl_sha256>"},
    "previous_revision": null,
    "deletion_candidates": []
  },
  "text_chunk": {
    "record_id": "<stable_record_id>",
    "logical_block_id": "<lesson_id>:<section_anchor>",
    "source_id": "course:domestika:<course_id>",
    "item_id": "<lesson_id>",
    "asset_id": "<native_vtt_id>",
    "source_revision": "<producing_source_revision>",
    "representation": "translation",
    "language": "en",
    "child_id": "<stable_record_id>",
    "parent_id": "<stable_parent_id>",
    "child_text": "<checked English prose>",
    "parent_text": "<checked enclosing section>",
    "context_text": "",
    "content_sha256": "<text_sha256>",
    "heading_path": "<module > lesson > concept>",
    "image_occurrence_ids": ["<figure_id>"],
    "provenance": {
      "child_spans": [{"text_char_range": [0, "<integer_end_offset>"], "asset_id": "<native_vtt_id>", "asset_sha256": "<vtt_sha256>", "canonical_url": "<safe_lesson_url>", "locator_type": "course_cues", "container_id": "<unit_id>", "lesson_id": "<lesson_id>", "cue_ids": ["<cue_id>"], "start_seconds": 130.0, "end_seconds": 245.0}],
      "parent_spans": [{"text_char_range": [0, "<integer_end_offset>"], "asset_id": "<native_vtt_id>", "asset_sha256": "<vtt_sha256>", "canonical_url": "<safe_lesson_url>", "locator_type": "course_cues", "container_id": "<unit_id>", "lesson_id": "<lesson_id>", "cue_ids": ["<all_parent_cue_ids>"], "start_seconds": 130.0, "end_seconds": 245.0}],
      "context_spans": []
    },
    "derivation": {"kind": "translation", "native_language": "<verified_language>", "transform_version": "<version>", "audit_id": "<passed_audit_id>", "removal_rules_sha256": "<rules_sha256>"},
    "quality": {"status": "verified", "open_blocking_findings": []},
    "token_count": "<integer_token_count>",
    "tokenizer": "cl100k_base",
    "chunker_version": "<version>",
    "embedding_input_sha256": "<hash_of_heading_context_child_input>",
    "embedding_space_id": "<configured_text_space_id>",
    "privacy": {"audience": "private", "privacy_scope_id": "<owner_scope>", "contains_credentials": false, "contains_signed_urls": false, "personal_data_status": "reviewed_clear", "allow_remote_processing": false, "allow_distribution": false}
  },
  "image_record": {
    "record_id": "<stable_image_record_id>",
    "figure_id": "<stable_figure_id>",
    "blob_id": "<owner_scope>:<image_sha256>",
    "source_id": "course:domestika:<course_id>",
    "item_id": "<lesson_id>",
    "source_revision": "<producing_source_revision>",
    "image_path": "images/<image_sha256>.jpg",
    "image_sha256": "<image_sha256>",
    "width_pixels": "<integer_width>",
    "height_pixels": "<integer_height>",
    "caption_status": "reviewed",
    "caption": "<original or checked caption>",
    "caption_provenance": [{"asset_id": "<lesson_markdown_id>", "asset_sha256": "<markdown_sha256>", "canonical_url": "<safe_lesson_url>", "locator_type": "reading_copy_figure_block", "figure_id": "<stable_figure_id>"}],
    "on_screen_text": "<checked on-screen text or explicit none/illegible status>",
    "context_record_ids": ["<stable_record_id>"],
    "context_excerpts": [{"record_id": "<stable_record_id>", "text": "<exact surrounding text>", "text_char_range": [0, "<integer_end_offset>"], "source_span_refs": ["<child_span_reference>"]}],
    "occurrences": [{"asset_id": "<reading_pdf_id>", "asset_sha256": "<pdf_sha256>", "canonical_url": "<safe_lesson_url>", "locator_type": "reading_copy_pdf_and_video", "page_index_1based": 8, "printed_page_label": null, "bbox_points": [40.0, 180.0, 550.0, 420.0], "coordinate_space": "unrotated_page", "page_size_points": [595.0, 842.0], "rotation_degrees": 0, "video_asset_id": "<mp4_id>", "video_sha256": "<mp4_sha256>", "lesson_id": "<lesson_id>", "requested_seconds": 192.0, "actual_frame_seconds": null, "actual_frame_time_reason": "not measured"}],
    "extraction": {"method": "reading_copy_frame", "tool_version": "<version>", "timestamp_status": "requested_only"},
    "quality": {"status": "verified", "open_blocking_findings": []},
    "privacy": {"audience": "private", "privacy_scope_id": "<owner_scope>", "contains_credentials": false, "contains_signed_urls": false, "personal_data_status": "reviewed_clear", "allow_remote_processing": false, "allow_distribution": false}
  }
}
```

A private KB intake may accept owner-authorized private course text; it must not add that material to the KB's distributable releases. Parent merging is confined to the same source item, representation, and privacy scope. Apply privacy filters to parent text, image delivery, exact-match search, chapter browsing, and catalog tools as well as ranked search. A public query must not receive a private hit through an alternative tool.

The concrete KB integration is a proposed `--handoff PATH` mode on `scripts/ingest_all.py`, dispatching to the new validator/intake boundary before model imports. Existing book ingestion remains a separate compatibility path during migration. Replace `BOOKS`-only discovery with a source registry for handoffs; retain `book`/`book_title` compatibility fields for book queries while adding generic `source_id`, `source_kind`, and `source_title`. Extend index payloads and all retrieval/export paths to carry provenance and privacy. Replace existence-based skipping with revision receipts. Do not route a handoff through both the old whole-book chunker and the shared source-aware chunker. This mode and these extensions do not exist in the inspected code; invoking them now would fail.

Keep existing text embeddings in their current space. The multimodal model, dimensionality, preprocessing, licensing, and deployment choice are **not selected** by this task. Do not assume its vectors share Jina's space merely because dimensions match. Store image vectors in a separate image collection keyed to text records; index captions/context with the text encoder and route image or text-to-image queries through the matching multimodal encoder. A vector space identifies its model revision, input role, dimension, normalization, and preprocessing. Qdrant also supports separate named vectors of different sizes, which is a later implementation option rather than a reason to mix incompatible vectors. [Qdrant vector documentation](https://qdrant.tech/documentation/manage-data/vectors/)

### Re-archiving and selective updates

An **idempotent** import has the same result when repeated with the same inputs. Maintain a local source revision ledger and dependency fingerprints. Use SHA-256 content fingerprints, stable source/item IDs, and stable block anchors. Derive retrieval record IDs from privacy scope, logical source, representation, and stable span/block identity; store content revision separately. For unchanged blocks shifted by a nearby insertion, reconcile old/new block fingerprints and occurrence order instead of assigning all-new positional IDs. Changed spans may receive new IDs, but unrelated items retain theirs.

1. Recollect authorized metadata and compare normalized inventories. A refreshed signed URL does not change content identity. Use a trustworthy immutable revision or validator when available; when none exists, mark source freshness unknown until bytes/content are checked. File existence and duration alone are not unchanged-content evidence.
2. Fetch only missing or demonstrably changed assets. Hash completed files; preserve transport/probe evidence privately. Re-extract only changed assets or assets whose extractor version changed. Changed PDF bytes may invalidate extraction even when the text later proves identical.
3. Compare normalized block, caption, image, and provenance hashes. A text embedding is reused only when its complete embedding input and embedding-space version match. Heading or enrichment changes can change that input. A corrected page/timestamp mapping without changed embedding input updates payload only. Unchanged image pixels reuse their image vector; changed caption/context updates the text representation and image payload, not the pixels' vector.
4. Stage text and image upserts and a revision acknowledgement under a run ID. An **upsert** inserts a new record or replaces the identified existing record. Publish a source revision only after all required writes/hashes are confirmed. A searchable source revision registry must keep incomplete revisions invisible. Use a journal and staged version records so restart can finish or discard a pending revision; do not claim that independent index writes are an atomic transaction.
5. Delete/tombstone obsolete occurrences only after authoritative, successful discovery of the same scope proves they were removed, and the new revision is activated. A tombstone marks a record inactive while retaining its history. A locked item, expired access, narrower selection, or failed collection is not deletion evidence. Retain the last verified content with its last-seen date and changed access state.
6. Record exact added/changed/reused/quarantined/removed record counts and KB receipt hashes. Garbage-collect old image blobs only after no retained occurrence references them. Completed handoff requires the consumer's matching source revision and counts, not merely files emitted by the producer.

Keep stable logical `record_id` separate from index storage identity: a staged storage ID includes the record's payload revision, so it cannot overwrite the old visible record before activation. The source revision registry records the active membership set and may reference unchanged records produced by earlier revisions. Their original producing revision/provenance remains intact. Retrieval reports the current source snapshot and the precise producing revision together. Changed metadata can create a new payload version using a cached embedding; no new model computation is needed when the embedding input is unchanged.

For this run, no indexing or live service change is authorized. Future CPU extraction that is heavy belongs under `~/kb-work/kbu-2026-10-07/R5/` on the specified workstation; no GPU/model job is implied by this design report. Resource policy must be a core execution setting, because the existing reading tool attempts Mac VideoToolbox acceleration before a software fallback. [D2]

## Domestika principle mapping

The rows below cover all **6 principles** and all **7 anti-pattern bullets** in the inspected Domestika `SKILL.md`. They are paraphrases of the rule content, with the destination and its future proving check. [D1]

| Existing rule | Where it lives in the reusable design | Required proving check |
|---|---|---|
| Principle 1: use existing user access; same-origin pages; never extract, print, store, or transmit cookies/account tokens. | Core access boundary plus Domestika/Coursera collector. Browser credentials stay in the browser; only ephemeral session handles cross into collection. | Credential fields rejected; collection restricted to selected source pages; export/log scan finds no cookies or tokens. |
| Principle 2: exposed playback only; stop on DRM, encryption, unavailable content, or missing requested language; no access evasion. | Core probe gate and adapter protection/access facts. Unknown protection cannot be treated as clear. | Protected/unknown media cannot enter fetch; missing required track yields an item-specific blocked result. No key extraction or decryption path. |
| Principle 3: confirm identity, totals, playable sample, languages, encryption, and material transfer requirements before the full run. | Discover/collect inventory, per-item probe, representative playback check, and core transfer plan. | Bulk fetch cannot begin without passing required probes; estimates identify their evidence, exact values when measured, or `not found`. |
| Principle 4: stable MP4/caption stem; requested and default-audio captions; PDF video markers with filenames, link, duration, transcript. | Core asset naming and document layout; adapter default/native language evidence. | Exact marker-to-asset mapping and caption deduplication; every selected lesson has required files and source text. Progressive adapters use their own language evidence. |
| Principle 5: manifest playback URLs stay local/private, outside archives and public bundles; retain privately only for resume. | Common schema's private transport projection and export validator. Sanitized manifest can travel; capability URLs cannot. | ZIP, PDF, handoff, and report inspections contain no signed URLs or private namespace; resumable private file is access-restricted. |
| Principle 6: claim only checked results; verify membership, media/audio tags, cues, rendered PDFs, and ZIP integrity. | Core verification receipts and independent archive/KB completion states. | Exact membership, media stream/language checks, cue parsing, rendered inspection, and ZIP cyclic redundancy check (CRC); KB receipt separately matches records. |
| Anti-pattern 1: do not archive inaccessible courses or infer one purchase grants another. | Selection and permission basis in manifest; collector access gate. | A different course identity or unavailable item blocks collection; inventory alone cannot authorize fetching. |
| Anti-pattern 2: no unrelated account crawl, other members' projects, or public use of private manifest. | Adapter scope allowlists, core privacy scope, and manifest projections. | Out-of-scope URLs/items rejected; no account/community-project traversal; private transport never offered as a KB source. |
| Anti-pattern 3: no DRM bypass, key extraction, access workaround, or silent quality/language/caption substitution. | Protection gate and immutable requested output requirements. | Missing exact requirement produces a failure/gap. An explicit approved selection change creates a new recorded scope rather than silently lowering quality. |
| Anti-pattern 4: PDFs, one unit, or a sample are not a complete archive. | Manifest selection/completeness and delivery status. | A partial run says selected-scope/partial; full-course status requires authoritative whole-course membership and all required checks. |
| Anti-pattern 5: no media URLs, cookies, or private manifest in ZIP/final response. | Secret exclusion and export validation across every artifact. | Scan generated HTML/PDF links, ZIP members, logs, and handoff recursively; only safe canonical source links remain. |
| Anti-pattern 6: never silently omit pages, transcripts, captions, or folders when totals differ. | Inventory reconciliation, expected member set, and gap ledger. | Any unaccounted mismatch fails completeness; locked, intentionally excluded, and failed items have separate explicit reasons. |
| Anti-pattern 7: native captions are primary; summary only under `Key points (derived)`; marketing removal changes rules, not hand-edited output. | Core faithful reading-copy policy, original/derived representation tags, and versioned per-adapter marketing rules. | Native transcript fidelity/audit; derived-summary tagging; rule-based removal log read in full; changing rules rebuilds affected derivatives. |

The reading-copy reference's coverage, frame captions, prose floor, and audit rules also remain applicable to course derivatives. Observed thresholds are **60 seconds** for permitted coverage gaps and **35%** for the prose-word floor unless a compression explanation is provided. These are safeguards, not proof of translation accuracy. An unresolved high/medium text finding blocks faithful distillation; figure-only findings follow the existing explicit limitations. [D3] Archive evidence must still retain excluded introductory/marketing content, while the reading derivative records each exclusion. Every source does not need Domestika's marketing patterns; rule files are adapter-specific data under shared audit/versioning mechanics.

## Key decisions and implementation checks

Grounding result: a whole Markdown-corpus search for `adapter interface`, `content.address`, and `idempotent...ingest` found relevant adapter discussion in `speedupyourpythonwithrust.md` and content-addressed storage in `pro-git.md`; the design adopts a small translating interface and stable content fingerprints. Primary project code determines the actual compatibility gaps. [K3] A file-path example or chapter mention is not treated as an existing ingestion API.

The principal trade-offs are explicit. A common core avoids duplicating packaging/privacy/verification rules but requires separating the current Domestika imports. Safe/private projections permit reproducible inventory without distributing playback capabilities but need validation of links inside content. Keeping original text and an English derivative uses more storage but preserves translation provenance. A separate image index avoids silently changing the existing text model; it requires a query router and linked image delivery. A staged source-revision ledger adds recovery work but prevents partial imports and stale deletions from masquerading as current results.

The future build should prove these named cases before deployment: `access_scope_and_no_cookie_export`; `encrypted_media_stops_before_transfer`; `coursera_progressive_and_locked_inventory`; `all_required_native_and_requested_captions`; `exact_archive_members_and_rendered_anchors`; `figure_caption_context_and_rotated_page_provenance`; `source_private_data_excluded_from_release`; `unchanged_rearchive_reuses_vectors`; `caption_only_change_preserves_image_vector`; `changed_source_updates_only_affected_items`; `failed_or_narrowed_discovery_never_deletes`; and `restart_between_text_and_image_writes_keeps_old_revision_visible`. These are proposed proving tests, **not tests run in R5**. They cover authorization, privacy boundaries, source changes, and restart behavior without relying on an already-running model or database.

Unresolved items are precise: Coursera embedded readings' collection method, exact caption-language inventory and native-language evidence, OpenAlex adapter implementation, a multimodal encoder/deployment choice, and end-to-end revision activation in the KB. Each is a build prerequisite for its corresponding capability, not a reason to invent current support. The durable design record is this report, as the task explicitly requires; no repository wiki was edited. Independent build approval/review remains for implementation, not a condition for delivering this read-only research artifact.

## Output sample

The following is real output from `python3 inspect_sources.py`, which reads source text and Python syntax without importing the inspected projects. It is stored in `source-inspection.txt`. The quantities are source-file/code observations, not archive-performance measurements or a running KB probe.

```text
domestika_reference_files=3
domestika_script_source_files=5
domestika_script_source_lines=1890
domestika_principles=6
domestika_antipatterns=7
kb_pipeline_steps=ingest,chunk,enrich,index
kb_parent_max_tokens=1900
kb_child_max_tokens=250
kb_clean_markdown_image_link_removal=true
kb_index_payload_keys=child_id,parent_id,child_text,context_text,parent_text,book,book_title,chapter,chapter_title,section,heading_path,chunk_type
litgraph_python_openalex_matches=0
litgraph_openalex_ingestion_code=not found
```

The first report acceptance run, `bash verify.sh`, produced the following real output:

```text
VERDICT: PASS
```

This check tests report structure, required words, sample presence, mapping table rows, and length; it does not prove the proposed implementation works. The same check is rerun after the final report edits; its output is retained in `verification.txt`.

## Sources

Local sources were inspected on **2026-10-10**. Their authoring/publication dates are **not found** unless a dated note is identified below. Paths are provided because these are owner-accessible local evidence, not public web pages. The Coursera observations have their own measurement date. External sources are primary documentation; where a page publication date was not found, that absence is explicit. All external pages were accessed on **2026-10-10**.

- **D1:** [Domestika SKILL.md](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/SKILL.md). Full rules, phase requirements, 6 principles, 7 anti-patterns; document date not found.
- **D2:** [collector](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/scripts/collect_domestika.js), [packager](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/scripts/package_domestika.py), [PDF layout](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/scripts/pdf_layout.py), [reading-copy tool](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/scripts/reading_copy.py), and [marketing rules](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/scripts/marketing_rules.json). Complete source files read; publication dates not found.
- **D3:** [operations](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/references/operations.md), [reading-copy method](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/references/reading-copy.md), and [audit loop](/Users/GaryT/Documents/Work/tools/agent-workflow/skills/domestika-course-archive/references/audit-loop.md). Complete references read; publication dates not found.
- **K1:** [KB pipeline guidance](/Users/GaryT/Documents/Work/tools/knowledge-base/CLAUDE.md:31) and [pipeline runner](/Users/GaryT/Documents/Work/tools/knowledge-base/scripts/ingest_all.py). Pipeline/status guidance; the guide includes a 2026-09-30 promotion note, not an overall publication date.
- **K2:** [ingest](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/ingest.py), [chunk](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/chunk.py), [index](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/index.py), [embedding helper](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/embedder.py), and [configuration](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/config.py). Current code behavior and constants; publication dates not found. Inspected as text only.
- **K3:** [adapter discussion](/Users/GaryT/Documents/Work/tools/knowledge-base/data/markdown/speedupyourpythonwithrust.md:4928) and [content-addressed storage discussion](/Users/GaryT/Documents/Work/tools/knowledge-base/data/markdown/pro-git.md:15626). Local KB search results; edition/publication dates were not established in this inspection.
- **L1:** [arXiv ingestion](/Users/GaryT/Documents/Work/products/litgraph/src/litgraph/sources/arxiv.py) and [seed ingestion](/Users/GaryT/Documents/Work/products/litgraph/src/litgraph/sources/seeds.py). Complete ingestion modules read; arXiv source includes a 2026-07-15 fetch-policy note; overall publication dates not found.
- **L2:** [command dispatch](/Users/GaryT/Documents/Work/products/litgraph/src/litgraph/cli.py:179) and [document schema](/Users/GaryT/Documents/Work/products/litgraph/src/litgraph/db.py). Current supported ingestion commands and stored fields; publication dates not found.
- **L3:** [Phase 1 design](/Users/GaryT/Documents/Work/products/litgraph/wiki/phase1-design.md:95) explicitly defers OpenAlex citation edges. The project active-work record dates Phase 1 completion to 2026-07-16. A read-only `rg` search found 0 Python files mentioning OpenAlex; that is scoped evidence, not proof about another checkout or remote installation.
- **Coursera:** Owner-supplied signed-in-browser findings in the R5 task brief, measured **2026-10-07**. Public evidence URL: **not found**. No Coursera endpoint or page was accessed for this report.
- [PyMuPDF Page API](https://pymupdf.readthedocs.io/en/latest/page.html): displayed images, occurrence rectangles, drawings/clustering, text coordinates, rotation, clipped raster rendering. Page publication date not found; individual API version notes are not the page date.
- [PyMuPDF image recipes](https://pymupdf.readthedocs.io/en/latest/recipes-images.html): image extraction and transparency-mask handling. Publication date not found.
- [PyMuPDF OCR guidance](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html): Tesseract-backed OCR and reuse of OCR text pages. Publication date not found.
- [pdfplumber README](https://github.com/jsvine/pdfplumber/blob/stable/README.md): layout objects, word rectangles, crops, and image reconstruction limitation. Publication date not found; `stable` is a moving reference.
- [EPUB 3.3 recommendation](https://www.w3.org/TR/2026/REC-epub-33-20260113/): package manifest and spine semantics. Document date: **2026-01-13**.
- [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html): version selection and publication/revision metadata. Publication date not found.
- [OpenAlex work attributes](https://help.openalex.org/data/works/attributes/): abstracts, referenced works, and open-access locations. Publication date not found.
- [GitHub tree API](https://docs.github.com/en/rest/git/trees): tree membership, object identifiers, read access, and truncated-tree handling. Publication date not found.
- [FFmpeg documentation](https://www.ffmpeg.org/ffmpeg.html): seeking and accurate-seek behavior. Publication date not found.
- [Qdrant vector documentation](https://qdrant.tech/documentation/manage-data/vectors/): separate named vector spaces and dimensionality. Publication date not found. Documentation only; no Qdrant service was contacted.
