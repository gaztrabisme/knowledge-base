"""Run the agent benchmark questions through the Claude Code CLI against oMLX."""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
for _path in (SCRIPTS_DIR, SCRIPTS_DIR.parent):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from agent_bench import SYSTEM_PROMPT, _load_api_key, cited_ids, parent_ids


ROOT = SCRIPTS_DIR.parent
OMLX_BASE_URL = "http://127.0.0.1:8000"
MODEL_SLOTS = (
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
)
TOKEN_PLACEHOLDER = "<redacted>"


def question_prompt(query: str) -> str:
    return f"{SYSTEM_PROMPT}\n\n{query}"


def mcp_config(server_root: Path, call_log: Path) -> dict:
    return {
        "mcpServers": {
            "kb": {
                "command": str(server_root / ".venv" / "bin" / "python"),
                "args": ["-m", "knowledge_base.server"],
                "cwd": str(server_root),
                "env": {
                    "PYTHONPATH": str(server_root),
                    "KB_CALL_LOG": str(call_log),
                },
            }
        }
    }


def build_command(prompt: str, model: str, config_path: Path, max_turns: int) -> list[str]:
    return [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--model", model,
        "--mcp-config", str(config_path),
        "--strict-mcp-config",
        "--tools", "",
        "--allowedTools", "mcp__kb",
        "--dangerously-skip-permissions",
        "--max-turns", str(max_turns),
        "--setting-sources", "",
    ]


def build_env(model: str, api_key: str, config_dir: Path) -> dict:
    env = dict(os.environ)
    env["ANTHROPIC_BASE_URL"] = OMLX_BASE_URL
    env["ANTHROPIC_AUTH_TOKEN"] = api_key
    for slot in MODEL_SLOTS:
        env[slot] = model
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    return env


def masked_env(env: dict) -> dict:
    masked = dict(env)
    if masked.get("ANTHROPIC_AUTH_TOKEN"):
        masked["ANTHROPIC_AUTH_TOKEN"] = TOKEN_PLACEHOLDER
    return masked


def usage_totals(usage: dict) -> tuple[int, int]:
    prompt = sum(int(usage.get(key) or 0) for key in (
        "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
    ))
    return prompt, int(usage.get("output_tokens") or 0)


def parse_stream(lines: list[str]) -> dict:
    turns = 0
    tool_names: list[str] = []
    summed_prompt = summed_completion = 0
    final_text = ""
    result_event = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            turns += 1
            message = event.get("message") or {}
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        tool_names.append(block.get("name"))
                    elif block.get("type") == "text" and block.get("text"):
                        final_text = block["text"]
            usage = message.get("usage")
            if isinstance(usage, dict):
                turn_prompt, turn_completion = usage_totals(usage)
                summed_prompt += turn_prompt
                summed_completion += turn_completion
        elif event.get("type") == "result":
            result_event = event
    if isinstance(result_event, dict) and isinstance(result_event.get("usage"), dict):
        prompt_tokens, completion_tokens = usage_totals(result_event["usage"])
    else:
        prompt_tokens, completion_tokens = summed_prompt, summed_completion
    if isinstance(result_event, dict) and result_event.get("result"):
        final_text = result_event["result"]
    return {
        "turns": turns,
        "tool_names": tool_names,
        "prompt_tokens_total": prompt_tokens,
        "completion_tokens_total": completion_tokens,
        "final_text": final_text,
        "result_event": result_event,
    }


def stream_stop_reason(timed_out: bool, result_event: dict | None) -> str:
    if timed_out:
        return "timeout"
    if not isinstance(result_event, dict):
        return "error"
    subtype = result_event.get("subtype")
    if subtype == "success":
        return "answer"
    if subtype == "error_max_turns":
        return "max_turns"
    return "error"


def read_calls(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def call_stats(call_rows: list[dict], positives: set[str]) -> dict:
    found = False
    first_hit_call = None
    invalid_calls = empty_results = tool_tokens_total = 0
    for index, row in enumerate(call_rows):
        if positives.intersection(row.get("parent_ids") or []):
            if not found:
                found = True
                first_hit_call = index + 1
        if row.get("error"):
            invalid_calls += 1
        if row.get("n_results") == 0:
            empty_results += 1
        tool_tokens_total += int(row.get("tokens") or 0)
    return {
        "found": found,
        "first_hit_call": first_hit_call,
        "invalid_calls": invalid_calls,
        "empty_results": empty_results,
        "tool_tokens_total": tool_tokens_total,
    }


def assemble_row(question: dict, summary: dict, stop_reason: str, call_rows: list[dict],
                 arm: str, model: str, wall_s: float) -> dict:
    positives = set(question.get("positive_parents", []))
    stats = call_stats(call_rows, positives)
    final_answer = summary["final_text"]
    ids = cited_ids(final_answer)
    cited = bool(positives.intersection(parent_ids([{"chunk_id": chunk_id} for chunk_id in ids])))
    return {
        "qid": question["qid"],
        "stratum": question.get("stratum", "golden"),
        "domain": question["domain"],
        "archetype": question["archetype"],
        "arm": arm,
        "model": model,
        "found": stats["found"],
        "cited": cited,
        "first_hit_call": stats["first_hit_call"],
        "n_calls": len(call_rows),
        "invalid_calls": stats["invalid_calls"],
        "empty_results": stats["empty_results"],
        "gave_up": stop_reason != "answer" or not final_answer.strip(),
        "prompt_tokens_total": summary["prompt_tokens_total"],
        "completion_tokens_total": summary["completion_tokens_total"],
        "tool_tokens_total": stats["tool_tokens_total"],
        "cited_ids": ids,
        "final_answer": final_answer,
        "stop_reason": stop_reason,
        "turns": summary["turns"],
        "wall_s": round(wall_s, 3),
        "calls": call_rows,
    }


def _drain(stream, sink: list) -> None:
    with stream:
        for line in stream:
            sink.append(line)


def run_claude(argv: list[str], env: dict, timeout_s: float) -> tuple[list[str], list[str], bool]:
    """Run claude, streaming its output; returns (stdout lines, stderr lines, timed_out)."""
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    try:
        proc = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", env=env,
        )
    except OSError as exc:
        return [], [f"failed to start claude: {exc}"], False
    readers = [
        threading.Thread(target=_drain, args=(proc.stdout, stdout_lines), daemon=True),
        threading.Thread(target=_drain, args=(proc.stderr, stderr_lines), daemon=True),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()
    for reader in readers:
        reader.join(timeout=5)
    return stdout_lines, stderr_lines, timed_out


def run_question(question: dict, args, api_key: str, output_path: Path) -> dict:
    qid = question["qid"]
    arm_slug = f"claude-{args.arm}-{args.model}"
    call_log = ROOT / "data/bench/calls" / arm_slug / f"{qid}.jsonl"
    transcript = ROOT / "data/bench/transcripts" / arm_slug / f"{qid}.jsonl"
    # One log file per question and completed qids are never retried, so a stale
    # log can only belong to an abandoned attempt at this same question.
    call_log.unlink(missing_ok=True)
    call_log.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=f"claude-bench-{qid}-") as workdir:
        workdir = Path(workdir)
        config_path = workdir / "mcp.json"
        config_path.write_text(
            json.dumps(mcp_config(Path(args.server_root), call_log), indent=2), encoding="utf-8"
        )
        argv = build_command(question_prompt(question["query"]), args.model, config_path, args.max_turns)
        config_dir = workdir / "config"
        config_dir.mkdir()
        env = build_env(args.model, api_key, config_dir)
        stdout_lines, stderr_lines, timed_out = run_claude(argv, env, args.timeout)
    summary = parse_stream(stdout_lines)
    stop_reason = stream_stop_reason(timed_out, summary["result_event"])
    final_answer = summary["final_text"]
    if not final_answer.strip():
        error_text = "\n".join(line for line in stderr_lines if line.strip())
        final_answer = error_text or f"claude produced no output (stop_reason={stop_reason})"
    call_rows = read_calls(call_log)
    row = assemble_row(question, summary, stop_reason, call_rows,
                       args.arm, args.model, time.perf_counter() - started)
    row["final_answer"] = final_answer
    transcript.write_text("".join(stdout_lines), encoding="utf-8")
    with output_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def load_questions(path: str, qids: str | None, limit: int | None) -> list[dict]:
    questions = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    if qids:
        wanted = set(qids.split(","))
        questions = [question for question in questions if question["qid"] in wanted]
    if limit is not None:
        questions = questions[:limit]
    return questions


def check_prerequisites(server_root: str) -> None:
    python_bin = Path(server_root) / ".venv" / "bin" / "python"
    if not python_bin.exists():
        sys.exit(f"server root has no {python_bin}")
    if shutil.which("claude") is None:
        sys.exit("claude CLI not found on PATH")


def dry_run(question: dict, args, api_key: str) -> None:
    qid = question["qid"]
    call_log = ROOT / "data/bench/calls" / f"claude-{args.arm}-{args.model}" / f"{qid}.jsonl"
    config = mcp_config(Path(args.server_root), call_log)
    argv = build_command(question_prompt(question["query"]), args.model, Path("<temp>/mcp.json"), args.max_turns)
    env = build_env(args.model, api_key, Path("<temp>/config"))
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    print(f"dry run for {qid}:")
    print(f"\ncommand:\n  {shlex.join(argv)}")
    print(f"\nmcp config (written to a temp file in a real run):\n{json.dumps(config, indent=2)}")
    print("\nenv (copy of os.environ with these overrides, ANTHROPIC_AUTH_TOKEN masked):")
    for key in sorted(("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", *MODEL_SLOTS,
                       "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "CLAUDE_CONFIG_DIR")):
        value = TOKEN_PLACEHOLDER if key == "ANTHROPIC_AUTH_TOKEN" else env[key]
        print(f"  {key}={value}")
    print("  ANTHROPIC_API_KEY removed")
    print("  CLAUDE_CODE_OAUTH_TOKEN removed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--server-root", required=True,
                        help="Git worktree whose knowledge_base.server is served")
    parser.add_argument("--qids", help="Comma-separated question IDs")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    check_prerequisites(args.server_root)
    questions = load_questions(args.questions, args.qids, args.limit)
    if not questions:
        sys.exit("no questions matched")
    api_key = _load_api_key()
    if args.dry_run:
        dry_run(questions[0], args, api_key)
        return

    output_path = ROOT / "data/bench/runs" / f"claude-{args.arm}-{args.model}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if output_path.exists():
        existing = {
            json.loads(line)["qid"]
            for line in output_path.read_text(encoding="utf-8").splitlines() if line
        }
    todo = [question for question in questions if question["qid"] not in existing]
    for index, question in enumerate(todo, 1):
        row = run_question(question, args, api_key, output_path)
        print(f"[{index}/{len(todo)}] {question['qid']} stop={row['stop_reason']} calls={row['n_calls']}",
              file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
