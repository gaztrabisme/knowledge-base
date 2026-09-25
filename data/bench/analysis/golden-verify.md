# Benchmark label verification

Reader: whoever interprets agent-benchmark results on `data/bench/questions_v2.jsonl`.
This records how the labels in that file were checked and what changed.

## Method

A Codex audit (judge A) proposed 258 extra correct passages and 15 wrong labels for the
150 bench questions. Each proposal became a (question, full passage) pair on a blinded
sheet, shuffled with 60 current labels (positive controls) and 60 unlabelled top-10
search candidates (negative controls). Graders saw opaque ids only, in directories
holding nothing but the sheet slice and the rubric (2 = directly answers, 1 = related or
partial, 0 = does not answer).

- Judge B: GLM lane (`glm-5.3-flash`), all 393 pairs.
- Reference: Claude subagents, a stratified 40 (10 per set), then every pair the rules
  sent to it.

Rules were fixed before grading: B counts only if calibrated; an extra is added when A and
B both give 2, else the reference decides; a label is removed when A and B both give 0,
else the reference decides; if B fails calibration the reference decides all 273.

## Judge B calibration

| Check | Value | Needed | Result |
|---|---:|---:|---|
| Positive controls graded 2 | 0.800 | ≥ 0.90 | FAIL |
| Negative controls graded 2 | 0.083 | ≤ 0.10 | pass |
| Agreement with reference, 2 vs not-2 (n=40) | 0.925 | ≥ 0.85 | pass |
| Cohen's κ, A vs B on 2 vs not-2 (n=273) | 0.044 | reported | — |

Judge B calibrated: **False**. Its grades are discarded; the reference decided all 273 extra and wrong-label pairs.

## Grade distributions (2 / 1 / 0)

| Set | n | Judge B | Reference |
|---|---:|---|---|
| extra | 258 | 138 / 116 / 4 | 83 / 160 / 15 (graded 258) |
| wrong | 15 | 5 / 6 / 4 | 4 / 5 / 6 (graded 15) |
| pos | 60 | 48 / 12 / 0 | 8 / 2 / 0 (graded 10) |
| neg | 60 | 5 / 43 / 12 | 0 / 3 / 7 (graded 10) |

## Result

- Questions dropped as ambiguous, unanswerable or leaky: 20.
- Extra passages added as correct answers: 77.
- Extras graded 2 but rejected because the question is specific to its own book: 0.
- Wrong labels removed: 5.
- Questions dropped for having no correct passage left: 2.
- Rows in `questions_v2.jsonl`: 128.

Every positive in `questions_v2.jsonl` carries its provenance (`original`, `added:A2,B2`
or `added:ref2`). Raw grades: `data/bench/analysis/verify/grades-B.jsonl`,
`grades-ref.jsonl`; key: `key.jsonl`.
