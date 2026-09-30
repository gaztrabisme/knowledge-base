# U6c flake check

Tested `u6c.sh` sequentially for runs 5–10 after the four prior runs, then ran two `u6c.sh` processes and one `u6.sh` process concurrently. Per-run top-level output was captured separately under `/tmp`.

| Run | Exit code | Duration | Note |
|---:|---:|---:|---|
| 1 | 0 | 124 s | Prior flake-hunt summary; sequential |
| 2 | 0 | 161 s | Prior flake-hunt summary; sequential |
| 3 | 0 | 236 s | Prior flake-hunt summary; sequential |
| 4 | 0 | 188 s | Prior flake-hunt summary; sequential |
| 5 | 0 | 154 s | Sequential; output `/tmp/u6c_run_5.txt` |
| 6 | 0 | 148 s | Sequential; output `/tmp/u6c_run_6.txt` |
| 7 | 0 | 144 s | Sequential; output `/tmp/u6c_run_7.txt` |
| 8 | 0 | 153 s | Sequential; output `/tmp/u6c_run_8.txt` |
| 9 | 0 | 150 s | Sequential; output `/tmp/u6c_run_9.txt` |
| 10 | 0 | 144 s | Sequential; output `/tmp/u6c_run_10.txt` |
| 11 | 0 | 169 s | Concurrent `u6c.sh`; output `/tmp/u6c_run_11.txt`; shared diagnostics rewritten |
| 12 | 0 | 169 s | Concurrent `u6c.sh`; output `/tmp/u6c_run_12.txt`; shared diagnostics rewritten |
| 13 | 0 | 32 s | Concurrent `u6.sh`; output `/tmp/u6c_run_13.txt`; shared diagnostics rewritten |

Not reproduced: all 13 recorded exits were 0. Remaining paths that can yield nonzero without a `FAIL:` line, most likely first: `u6c.sh`'s first Python heredoc exits 1 when its `bad` index predicate is true, after printing only per-book counts; interpreter, JSON, or data-shape errors in that heredoc can also exit without `FAIL:`. Standalone `u6.sh`'s first Python heredoc can exit 1 on its manifest/chunk/heading predicate or an exception without its own `FAIL:` line, but `u6c.sh` wraps that command and prints `FAIL: u6`; `u6.sh` also ignores `check_headings.py`'s return code and only consumes its stdout JSON. Standalone `u4.sh` can exit 1 after its plain acceptance summary (`ok` false), on an exception, or on a missing argument under `set -u`, but calls from `u6c.sh` are caught and print `FAIL: u4 <slug>`. Audit/regression failures are explicitly wrapped with `FAIL:`; no other child exit status leaks past the explicit final `exit $fail`. In the concurrent batch, `/tmp/u6c_u6.txt`, `/tmp/u6_reg.txt`, and `/tmp/u6_audit.txt` were rewritten (mtime changed; regression/audit SHA-256 changed, u6 summary content hash stayed the same), so their shared diagnostic contents are clobberable; all three exit statuses remained 0, regression reported 15/15 with no differences, and audit reported 0 unexcepted flags.
