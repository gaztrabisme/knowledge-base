"""Unit tests for claude_bench parsing, using synthetic fixtures only."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import claude_bench


QUESTION = {
    "qid": "h0002",
    "query": "When is an approximate result acceptable?",
    "domain": "distributed",
    "archetype": "baseline",
    "stratum": "golden",
    "positive_parents": ["crypto-101-p12"],
}


def assistant_event(blocks, usage):
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": blocks, "usage": usage},
    }


def result_event(subtype="success", result_text=None, usage=None, is_error=False):
    event = {"type": "result", "subtype": subtype, "is_error": is_error, "num_turns": 3}
    if result_text is not None:
        event["result"] = result_text
    if usage is not None:
        event["usage"] = usage
    return event


def tool_block(name):
    return {"type": "tool_use", "id": "toolu_01", "name": name, "input": {}}


def text_block(text):
    return {"type": "text", "text": text}


class ParseStreamTests(unittest.TestCase):
    def test_result_event_usage_text_and_tool_order(self):
        lines = [
            json.dumps({"type": "system", "subtype": "init", "session_id": "s1"}),
            json.dumps(assistant_event([tool_block("mcp__kb__search")],
                                       {"input_tokens": 100, "output_tokens": 20,
                                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})),
            json.dumps({"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "toolu_01", "content": "[]"}]}}),
            json.dumps(assistant_event([tool_block("mcp__kb__read")],
                                       {"input_tokens": 200, "output_tokens": 30,
                                        "cache_read_input_tokens": 400, "cache_creation_input_tokens": 50})),
            json.dumps(assistant_event([text_block("Roughly when latency matters.\nCITED: crypto-101-p12-c3")],
                                       {"input_tokens": 300, "output_tokens": 27,
                                        "cache_read_input_tokens": 600, "cache_creation_input_tokens": 60})),
            json.dumps(result_event(
                result_text="Roughly when latency matters.\nCITED: crypto-101-p12-c3",
                usage={"input_tokens": 600, "output_tokens": 77,
                       "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 110},
            )),
        ]

        summary = claude_bench.parse_stream(lines)

        self.assertEqual(summary["turns"], 3)
        self.assertEqual(summary["tool_names"], ["mcp__kb__search", "mcp__kb__read"])
        # Result-event usage wins: input + cache read + cache creation, and output.
        self.assertEqual(summary["prompt_tokens_total"], 600 + 1000 + 110)
        self.assertEqual(summary["completion_tokens_total"], 77)
        self.assertEqual(summary["final_text"], "Roughly when latency matters.\nCITED: crypto-101-p12-c3")
        self.assertEqual(claude_bench.stream_stop_reason(False, summary["result_event"]), "answer")

    def test_without_result_event_usage_is_summed_per_message(self):
        lines = [
            json.dumps(assistant_event([tool_block("mcp__kb__search")],
                                       {"input_tokens": 100, "output_tokens": 20,
                                        "cache_read_input_tokens": 5, "cache_creation_input_tokens": 6})),
            json.dumps(assistant_event([text_block("partial answer")],
                                       {"input_tokens": 111, "output_tokens": 22,
                                        "cache_read_input_tokens": 7, "cache_creation_input_tokens": 8})),
        ]

        summary = claude_bench.parse_stream(lines)

        self.assertEqual(summary["turns"], 2)
        self.assertEqual(summary["prompt_tokens_total"], 100 + 5 + 6 + 111 + 7 + 8)
        self.assertEqual(summary["completion_tokens_total"], 20 + 22)
        self.assertEqual(summary["final_text"], "partial answer")
        self.assertIsNone(summary["result_event"])
        self.assertEqual(claude_bench.stream_stop_reason(False, summary["result_event"]), "error")
        self.assertEqual(claude_bench.stream_stop_reason(True, summary["result_event"]), "timeout")

    def test_malformed_lines_are_skipped(self):
        summary = claude_bench.parse_stream(["not json", "", json.dumps(
            result_event(result_text="done"))])
        self.assertEqual(summary["final_text"], "done")
        self.assertEqual(summary["turns"], 0)

    def test_stop_reason_mapping(self):
        self.assertEqual(claude_bench.stream_stop_reason(False, result_event("success")), "answer")
        self.assertEqual(
            claude_bench.stream_stop_reason(False, result_event("error_max_turns", is_error=True)),
            "max_turns",
        )
        self.assertEqual(claude_bench.stream_stop_reason(False, result_event("error_during_execution",
                                                                             is_error=True)), "error")
        self.assertEqual(claude_bench.stream_stop_reason(False, None), "error")
        self.assertEqual(claude_bench.stream_stop_reason(True, None), "timeout")


def write_call_log(rows) -> list[dict]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "h0002.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        return claude_bench.read_calls(path)


class CallLogTests(unittest.TestCase):
    def test_read_calls_and_stats_against_synthetic_log(self):
        rows = [
            {"tool": "search", "args": {"query": "approximate"}, "error": None, "n_results": 5,
             "tokens": 900, "chunk_ids": ["crypto-101-p11-c0"], "parent_ids": ["crypto-101-p11"]},
            {"tool": "read", "args": {"chunk_id": "crypto-101-p12-c3"}, "error": "boom", "n_results": 0,
             "tokens": 1200, "chunk_ids": [], "parent_ids": ["crypto-101-p12"]},
            {"tool": "search", "args": {"query": "retry"}, "error": None, "n_results": 3,
             "tokens": 300, "chunk_ids": ["other-p1-c0"], "parent_ids": ["other-p1"]},
        ]
        log = write_call_log(rows)

        stats = claude_bench.call_stats(log, set(QUESTION["positive_parents"]))

        self.assertEqual(log[0]["tool"], "search")
        self.assertEqual(stats, {
            "found": True,
            "first_hit_call": 2,
            "invalid_calls": 1,
            "empty_results": 1,
            "tool_tokens_total": 900 + 1200 + 300,
        })

    def test_missing_log_file_reads_as_no_calls(self):
        self.assertEqual(claude_bench.read_calls(Path("/nonexistent/x.jsonl")), [])

    def test_miss_when_no_parent_intersects(self):
        rows = [{"tool": "search", "args": {}, "error": None, "n_results": 2,
                 "tokens": 10, "chunk_ids": ["other-p1-c0"], "parent_ids": ["other-p1"]}]

        stats = claude_bench.call_stats(rows, set(QUESTION["positive_parents"]))

        self.assertEqual(stats["found"], False)
        self.assertIsNone(stats["first_hit_call"])


class AssembleRowTests(unittest.TestCase):
    def build_summary(self, final_text, usage, subtype="success", with_result=True):
        lines = [
            json.dumps(assistant_event([tool_block("mcp__kb__search")],
                                       {"input_tokens": 10, "output_tokens": 5,
                                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})),
            json.dumps(assistant_event([text_block(final_text)],
                                       {"input_tokens": 10, "output_tokens": 5,
                                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})),
        ]
        if with_result:
            lines.append(json.dumps(result_event(subtype, result_text=final_text, usage=usage)))
        return claude_bench.parse_stream(lines)

    ROW_KEYS = {
        "qid", "stratum", "domain", "archetype", "arm", "model",
        "found", "cited", "first_hit_call", "n_calls", "invalid_calls", "empty_results", "gave_up",
        "prompt_tokens_total", "completion_tokens_total", "tool_tokens_total",
        "cited_ids", "final_answer", "stop_reason", "turns", "wall_s", "calls",
    }

    def test_answer_row_found_cited_and_tokens(self):
        final_text = "Approximation is fine under bounded staleness.\nCITED: crypto-101-p12-c3"
        summary = self.build_summary(
            final_text, {"input_tokens": 600, "output_tokens": 77,
                         "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 110})
        call_rows = [
            {"tool": "search", "args": {}, "error": None, "n_results": 5,
             "tokens": 900, "chunk_ids": ["crypto-101-p11-c0"], "parent_ids": ["crypto-101-p11"]},
            {"tool": "read", "args": {}, "error": None, "n_results": 1,
             "tokens": 1200, "chunk_ids": ["crypto-101-p12-c3"], "parent_ids": ["crypto-101-p12"]},
        ]

        row = claude_bench.assemble_row(QUESTION, summary, "answer", call_rows, "T", "m1", 12.3456)

        self.assertEqual(set(row), self.ROW_KEYS)
        self.assertTrue(row["found"])
        self.assertEqual(row["first_hit_call"], 2)
        self.assertTrue(row["cited"])
        self.assertEqual(row["cited_ids"], ["crypto-101-p12-c3"])
        self.assertFalse(row["gave_up"])
        self.assertEqual(row["stop_reason"], "answer")
        self.assertEqual(row["n_calls"], 2)
        self.assertEqual(row["tool_tokens_total"], 2100)
        self.assertEqual(row["prompt_tokens_total"], 600 + 1000 + 110)
        self.assertEqual(row["completion_tokens_total"], 77)
        self.assertEqual(row["turns"], 2)
        self.assertEqual(row["wall_s"], 12.346)
        self.assertEqual(row["calls"], call_rows)
        self.assertEqual(row["arm"], "T")
        self.assertEqual(row["model"], "m1")

    def test_uncited_answer_with_missed_retrieval(self):
        summary = self.build_summary(
            "I do not know.", {"input_tokens": 50, "output_tokens": 4,
                               "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0})
        call_rows = [{"tool": "search", "args": {}, "error": None, "n_results": 2,
                      "tokens": 10, "chunk_ids": ["other-p1-c0"], "parent_ids": ["other-p1"]}]

        row = claude_bench.assemble_row(QUESTION, summary, "answer", call_rows, "T", "m1", 1.0)

        self.assertFalse(row["found"])
        self.assertIsNone(row["first_hit_call"])
        self.assertFalse(row["cited"])
        self.assertEqual(row["cited_ids"], [])
        self.assertEqual(row["prompt_tokens_total"], 50)
        self.assertEqual(row["completion_tokens_total"], 4)

    def test_max_turns_row_counts_as_given_up(self):
        summary = self.build_summary(
            "partial\nCITED: crypto-101-p12-c3",
            {"input_tokens": 900, "output_tokens": 90,
             "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10},
            subtype="error_max_turns", with_result=True,
        )

        row = claude_bench.assemble_row(QUESTION, summary, "max_turns", [], "T", "m1", 2.0)

        self.assertEqual(row["stop_reason"], "max_turns")
        self.assertTrue(row["gave_up"])
        self.assertTrue(row["cited"])
        self.assertEqual(row["n_calls"], 0)
        self.assertEqual(row["prompt_tokens_total"], 1010)

    def test_duplicate_citations_are_deduplicated(self):
        summary = self.build_summary(
            "text\nCITED: crypto-101-p12-c3, crypto-101-p12-c3",
            {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0,
             "cache_creation_input_tokens": 0})

        row = claude_bench.assemble_row(QUESTION, summary, "answer", [], "T", "m1", 0.1)

        self.assertEqual(row["cited_ids"], ["crypto-101-p12-c3"])


class ConfigAndEnvTests(unittest.TestCase):
    def test_mcp_config_shape(self):
        config = claude_bench.mcp_config(Path("/srv/kb"), Path("/repo/data/bench/calls/x/h0002.jsonl"))

        server = config["mcpServers"]["kb"]
        self.assertEqual(server["command"], "/srv/kb/.venv/bin/python")
        self.assertEqual(server["args"], ["-m", "knowledge_base.server"])
        self.assertEqual(server["cwd"], "/srv/kb")
        self.assertEqual(server["env"], {
            "PYTHONPATH": "/srv/kb",
            "KB_CALL_LOG": "/repo/data/bench/calls/x/h0002.jsonl",
        })

    def test_command_flags(self):
        argv = claude_bench.build_command("prompt text", "model-x", Path("/tmp/mcp.json"), 7)

        self.assertEqual(argv[0], "claude")
        self.assertEqual(argv[1:3], ["-p", "prompt text"])
        for flag in ("--output-format", "stream-json", "--verbose", "--model", "model-x",
                     "--mcp-config", "/tmp/mcp.json", "--strict-mcp-config", "--tools", "",
                     "--allowedTools", "mcp__kb", "--dangerously-skip-permissions",
                     "--max-turns", "7", "--setting-sources", ""):
            self.assertIn(flag, argv)

    def test_build_env_overrides_and_removals(self):
        import os

        with tempfile.TemporaryDirectory() as directory:
            env = claude_bench.build_env("model-x", "secret", Path(directory))

        self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://127.0.0.1:8000")
        self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "secret")
        for slot in claude_bench.MODEL_SLOTS:
            self.assertEqual(env[slot], "model-x")
        self.assertEqual(env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"], "1")
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], directory)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", env)
        # Unrelated environment is preserved.
        self.assertEqual(env["PATH"], os.environ["PATH"])

    def test_masked_env_hides_token(self):
        masked = claude_bench.masked_env({"ANTHROPIC_AUTH_TOKEN": "secret-value", "OTHER": "x"})

        self.assertEqual(masked["ANTHROPIC_AUTH_TOKEN"], claude_bench.TOKEN_PLACEHOLDER)
        self.assertEqual(masked["OTHER"], "x")


if __name__ == "__main__":
    unittest.main()
