# Sanity Set Review Report (v9)

This report documents the review of all 29 retrieval test queries in `sanity.jsonl` evaluated against the four evaluation rules:
- **R1 On-topic**: The query asks about a core subject of the book.
- **R2 Self-contained**: The query is understandable independently without relying on an unstated scenario or passage-specific anecdote.
- **R3 Label answers**: The labelled chunk text actually contains the substantive answer rather than merely related text or headers.
- **R4 Label complete**: The positive child IDs include all passages in the book that answer the query as well or better.

---

## Verdict Summary

- **Total Rows**: 29
- **Keep**: 25
- **Fix-Query**: 1 (Row 0)
- **Fix-Label**: 2 (Rows 5 and 28)
- **Drop**: 1 (Row 8)

---

## Table of All 29 Rows

| # | Book | Verdict | Reason |
|---|------|---------|--------|
| 0 | `pmbok-guide-7e` | **fix-query** | Fails R1/R2 by asking about an incidental airport case study; rewritten to focus on simulation for complex systems. |
| 1 | `agentic-mesh` | **keep** | Passes R1–R4; directly specifies trust workbench for governance evidence and operator workbench for recovery controls. |
| 2 | `bargaining-for-advantage` | **keep** | Passes R1–R4; answers Quadrant II relationship bargaining conduct guidelines. |
| 3 | `container-security` | **keep** | Passes R1–R4; explains image digest references avoiding re-pulls and image signatures verifying provenance. |
| 4 | `critical-thinking-about-research` | **keep** | Passes R1–R4; details selecting multidisciplinary literature indexes and choosing search terms for syntheses. |
| 5 | `designing-ai-interfaces` | **fix-label** | R3/R4 failed because p47-c2 omitted the name of tokenization; added p47-c0 which defines the transformation. |
| 6 | `flawless-consulting` | **keep** | Passes R1–R4; specifies rules for consulting with a stone (withholding emotional reactions and dropping expectations). |
| 7 | `getting-to-yes` | **keep** | Passes R1–R4; uses job offer comparison to explain how outside alternatives (BATNA) establish negotiating power. |
| 8 | `hbr-guide-business-writing` | **drop** | Fails R1/R2; off-topic performance appraisal table fragment spanning partial rubrics for which no fair query can be written. |
| 9 | `hands-on-site-reliability-engineering` | **keep** | Passes R1–R4; documents cross-application postmortem review attendees (dev leads, support leads, senior managers). |
| 10 | `head-first-pmp` | **keep** | Passes R1–R4; explains why early specification reviews in quality planning cost much less than detecting bugs in final testing. |
| 11 | `high-performance-browser-networking` | **keep** | Passes R1–R4; identifies Navigation Timing API (performance.timing) capturing DNS and TCP connection metrics for real users. |
| 12 | `how-to-read-a-paper` | **keep** | Passes R1–R4; outlines assessing clinical guideline evidence content, development process, and presentation (AGREE tool). |
| 13 | `key-account-management` | **keep** | Passes R1–R4; explains how annual reports and financial sources reveal customer priorities and ratios to assist them. |
| 14 | `meddicc` | **keep** | Passes R1–R4; explains keeping the Economic Buyer informed on implementation to secure future renewals, upsells, and references. |
| 15 | `practical-cloud-security` | **keep** | Passes R1–R4; details agent-based vulnerability scanners using outbound-only connections and automated deployment benefits. |
| 16 | `privacy-in-context` | **keep** | Passes R1–R4; details contextual integrity parameters (actors, information types, transmission principles) covarying together. |
| 17 | `project-planning-scheduling-control` | **keep** | Passes R1–R4; shows that modal time represents typical duration more accurately than arithmetic mean for skewed distributions. |
| 18 | `python-for-devops` | **keep** | Passes R1–R4; explains container OS-level virtualization where the host kernel isolates user-space instances. |
| 19 | `real-world-software-development` | **keep** | Passes R1–R4; explains using an Action interface to decouple the business rules engine from concrete operations. |
| 20 | `research-ethics-integrity-social-scientists` | **keep** | Passes R1–R4; details direct assistance for high-risk research communities, such as funding health services and back-office support. |
| 21 | `research-methods-psychology` | **keep** | Passes R1–R4; details obscuring factors in null effects (weak manipulations, insensitive measures, ceiling/floor effects, measurement error). |
| 22 | `selling-to-big-companies` | **keep** | Passes R1–R4; explains studying client business issues and applying expertise and ideas rather than pitching product offerings. |
| 23 | `software-engineering-at-google` | **keep** | Passes R1–R4; defines fake fidelity to API contracts and warns of false test passes when fakes deviate from real dependencies. |
| 24 | `art-of-assembly-language` | **keep** | Passes R1–R4; explains HLA external directive syntax to explicitly assign external linker names avoiding global symbol conflicts. |
| 25 | `challenger-sale` | **keep** | Passes R1–R4; identifies sales representative professionalism as the primary driver of end-user and influencer loyalty. |
| 26 | `flawless-consulting-fieldbook-companion-2e` | **keep** | Passes R1–R4; emphasizes that organizational labor belongs to the client and advisor should maintain objective detachment. |
| 27 | `new-ethics-of-journalism` | **keep** | Passes R1–R4; explains that Kony 2012's viral reach resulted from years of deliberate marketing rather than spontaneous luck. |
| 28 | `value-based-fees` | **fix-label** | R3 failed because p76-c0 only introduces buyer psychology; replaced with p76-c1 which details refusing premature fee discussions. |

---

## Query Modifications (fix-query)

| Row | Book | Original Query | Reviewed Query |
|:---:|:-----|:---------------|:---------------|
| 0 | `pmbok-guide-7e` | For a planned airport with uncertain retail demand, how could the team estimate likely customer behavior before those facilities exist? | When managing project complexity, how can a team use simulation to understand how system components will behave? |

### Detailed Notes on Query Fixes

#### Row 0 (`pmbok-guide-7e`)
- **Original Passage**: `pmbok-guide-7e-p46-c7`
- **Rule Violations**:
  - **R1 (On-topic)**: PMBOK Guide is a general project management framework, not a manual for predicting retail consumer behavior at airports.
  - **R2 (Self-contained)**: The airport facility is an incidental case example in an illustrative bullet point under "Simulation".
- **Resolution**: Rewritten to ask generally about using simulation to understand complex system components, which directly matches the conceptual content of `pmbok-guide-7e-p46-c7` without copying distinctive phrasing.

---

## Label and Exclusion Modifications (fix-label & drop)

### Row 5 (`designing-ai-interfaces`) — fix-label
- **Query**: "What transformation converts written input into discrete numeric units that a language model can process?"
- **Original Positives**: `["designing-ai-interfaces-p47-c2"]`
- **Reviewed Positives**: `["designing-ai-interfaces-p47-c0", "designing-ai-interfaces-p47-c2"]`
- **Rule Violations**: R3/R4. Chunk `p47-c2` describes token IDs and RGB space embeddings but never defines or names the transformation (tokenization). Chunk `p47-c0` specifically defines tokenization as the technical step converting human language into machine-readable numbers for LLMs. Both passages are included for completeness.

### Row 8 (`hbr-guide-business-writing`) — drop
- **Original Query**: "Which observable work habits help distinguish strong performance from repeated shortfalls when deadlines or urgent tasks arise?"
- **Original Positives**: `["hbr-guide-business-writing-p63-c5"]`
- **Rule Violations**: R1/R2. The book focuses on business writing, not HR management evaluation. Furthermore, chunk `p63-c5` is a mid-table fragment that begins without a header category and is truncated across multiple rating rubrics. As an uncontained fragment, no fair retrieval query can be written for it.

### Row 28 (`value-based-fees`) — fix-label
- **Query**: "How can a consultant keep a fee discussion focused on the customer’s expected benefit when the buyer tries to make it only about cost?"
- **Original Positives**: `["value-based-fees-p76-c0"]`
- **Reviewed Positives**: `["value-based-fees-p76-c1"]`
- **Rule Violations**: R3. Chunk `p76-c0` merely introduces the section heading and explains the buyer's psychology for wanting to discuss fees early. It does not answer *how* to maintain the focus on value. Chunk `p76-c1` provides the explicit strategy: refusing to negotiate fees prematurely and insisting on establishing clear ROI results before quoting costs.
