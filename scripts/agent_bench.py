"""Run a tool-using local model over the agent benchmark questions."""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

from openai import AsyncOpenAI

from knowledge_base import calllog, server


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8000/v1"
SYSTEM_PROMPT = (
    "You answer software engineering questions using the knowledge-base tools. "
    "Search before answering. Finish with a short answer and a final line "
    "`CITED: <chunk_id>, ...` listing the chunk_ids that support it."
)
CHUNK_ID_RE = re.compile(r"[A-Za-z0-9_.-]+-p\d+-c\d+")
TOOL_LOCK = asyncio.Lock()
WRITE_LOCK = asyncio.Lock()
_ENCODER = None


def token_count(value: object) -> int:
    global _ENCODER
    if _ENCODER is None:
        import tiktoken

        _ENCODER = tiktoken.get_encoding("cl100k_base")
    serialized = json.dumps(value)
    return len(_ENCODER.encode(serialized))


def result_error(value: object) -> str | None:
    if isinstance(value, str) and "not found" in value.lower():
        return value
    errors: list[str] = []

    def visit(item: object) -> None:
        if isinstance(item, dict):
            if "error" in item:
                errors.append(str(item["error"]))
            for child in item.values():
                if isinstance(child, (dict, list)):
                    visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return "; ".join(dict.fromkeys(errors)) or None


def parent_ids(value: object) -> set[str]:
    found: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, dict):
            parent_id = item.get("parent_id")
            if isinstance(parent_id, str):
                found.add(parent_id)
            chunk_id = item.get("chunk_id")
            if isinstance(chunk_id, str):
                match = re.match(r"^(.+)-p(\d+)-c\d+$", chunk_id)
                if match:
                    found.add(f"{match.group(1)}-p{match.group(2)}")
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return found


def is_empty_result(value: object) -> bool:
    if isinstance(value, dict) and isinstance(value.get("results"), list):
        return value["results"] == []
    return isinstance(value, list) and value == []


def result_count(value: object) -> int:
    if isinstance(value, dict) and isinstance(value.get("results"), list):
        return len(value["results"])
    if isinstance(value, list):
        return len(value)
    return int(value is not None and value != "")


def cited_ids(answer: str) -> list[str]:
    cited_line = None
    for line in answer.splitlines():
        # Models often format the line as markdown ("**CITED:** ...", "- CITED: ...").
        bare = line.strip().lstrip("*_`#>- ").replace("*", "")
        if bare.lower().startswith("cited:"):
            cited_line = bare.split(":", 1)[1]
    return list(dict.fromkeys(CHUNK_ID_RE.findall(cited_line or "")))


def _load_api_key() -> str:
    settings_path = Path.home() / ".omlx" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    return settings["auth"]["api_key"]


def _tool_definitions(function_tools: list) -> tuple[list[dict], dict[str, object]]:
    offered = []
    by_name = {}
    for tool in function_tools:
        by_name[tool.name] = tool
        offered.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        })
    return offered, by_name


async def _chat(client, model: str, messages: list[dict], tools: list[dict], thinking: bool,
                tool_choice: str = "auto"):
    return await client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        max_tokens=2048,
        extra_body={"chat_template_kwargs": {"enable_thinking": thinking}},
    )


async def _run_question(question: dict, args, client, offered_tools, tools_by_name) -> dict:
    qid = question["qid"]
    positive = set(question.get("positive_parents", []))
    calllog.set_run_id(f"{args.arm}|{args.model}|{qid}")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question["query"]},
    ]
    transcript = list(messages)
    calls: list[dict] = []
    found = False
    first_hit_call = None
    tokens_to_first_hit = None
    prompt_total = completion_total = max_prompt = tool_tokens_total = 0
    invalid_calls = empty_results = turns = 0
    final_answer = ""
    stop_reason = "no_answer"
    cap_reached = False
    run_error = None
    started = time.perf_counter()

    while True:
        turns += 1
        try:
            response = await _chat(client, args.model, messages, offered_tools, args.thinking == "on")
        except Exception as exc:
            stop_reason = "error"
            run_error = str(exc)
            break

        choice = response.choices[0]
        message = choice.message.model_dump(exclude_none=True)
        transcript.append({"role": "assistant", **message})
        usage = response.usage
        turn_prompt = int(usage.prompt_tokens) if usage and usage.prompt_tokens is not None else 0
        turn_completion = int(usage.completion_tokens) if usage and usage.completion_tokens is not None else 0
        prompt_total += turn_prompt
        completion_total += turn_completion
        max_prompt = max(max_prompt, turn_prompt)
        messages.append({"role": "assistant", **message})
        tool_calls = choice.message.tool_calls or []
        if choice.finish_reason != "tool_calls":
            tool_calls = []
        if not tool_calls:
            final_answer = message.get("content") or ""
            stop_reason = "answer" if final_answer.strip() else "no_answer"
            break

        # Run each function call serially across every question in this process.
        for tool_index, tool_call in enumerate(tool_calls):
            if len(calls) >= args.max_calls:
                cap_reached = True
                for pending in tool_calls[tool_index:]:
                    notice = "Error: maximum tool call limit reached."
                    messages.append({"role": "tool", "tool_call_id": pending.id, "content": notice})
                    transcript.append({"role": "tool", "tool_call_id": pending.id,
                                       "name": pending.function.name, "content": notice})
                break
            name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"
            error = None
            output_text = ""
            raw_result = None
            parsed_args = None
            result_tokens = 0
            invalid = False
            try:
                parsed_args = json.loads(raw_args)
                if not isinstance(parsed_args, dict):
                    raise ValueError("tool arguments must be a JSON object")
            except (json.JSONDecodeError, ValueError) as exc:
                error = f"Invalid tool arguments: {exc}"
                invalid = True
                output_text = error
            else:
                tool = tools_by_name.get(name)
                if tool is None:
                    error = f"Unknown tool: {name}"
                    invalid = True
                    output_text = error
                else:
                    try:
                        async with TOOL_LOCK:
                            raw_result = await asyncio.to_thread(tool.fn, **parsed_args)
                        result_json = json.dumps(raw_result)
                        result_tokens = token_count(raw_result)
                        error = result_error(raw_result)
                        if error:
                            invalid = True
                        if is_empty_result(raw_result):
                            empty_results += 1
                        if result_tokens > args.max_tool_tokens:
                            error = (
                                f'Error: MCP tool "{name}" response ({result_tokens} tokens) exceeds '
                                f"maximum allowed tokens ({args.max_tool_tokens})."
                            )
                            invalid = True
                            output_text = error
                        else:
                            output_text = result_json
                            if not found and positive.intersection(parent_ids(raw_result)):
                                found = True
                                first_hit_call = len(calls) + 1
                                tokens_to_first_hit = prompt_total + completion_total
                    except Exception as exc:
                        error = str(exc)
                        invalid = True
                        output_text = f"Tool error: {error}"
                        result_tokens = token_count(output_text)
            if parsed_args is None:
                parsed_args = {"_raw": raw_args}
            if result_tokens == 0:
                result_tokens = token_count(output_text)
            tool_tokens_total += result_tokens
            if invalid:
                invalid_calls += 1
            n_results = result_count(raw_result)
            calls.append({
                "tool": name,
                "args": parsed_args,
                "error": error,
                "n_results": n_results,
                "tokens": result_tokens,
            })
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": output_text})
            transcript.append({"role": "tool", "tool_call_id": tool_call.id,
                               "name": name, "content": output_text})
            if len(calls) >= args.max_calls:
                cap_reached = True
                for pending in tool_calls[tool_index + 1:]:
                    notice = "Error: maximum tool call limit reached."
                    messages.append({"role": "tool", "tool_call_id": pending.id, "content": notice})
                    transcript.append({"role": "tool", "tool_call_id": pending.id,
                                       "name": pending.function.name, "content": notice})
                break

        if cap_reached:
            messages.append({"role": "user", "content": "Give your final answer now using the retrieved context."})
            transcript.append(messages[-1])
            turns += 1
            try:
                response = await _chat(client, args.model, messages, offered_tools,
                                       args.thinking == "on", tool_choice="none")
                choice = response.choices[0]
                message = choice.message.model_dump(exclude_none=True)
                transcript.append({"role": "assistant", **message})
                usage = response.usage
                if usage:
                    prompt_total += int(usage.prompt_tokens or 0)
                    completion_total += int(usage.completion_tokens or 0)
                    max_prompt = max(max_prompt, int(usage.prompt_tokens or 0))
                final_answer = message.get("content") or ""
                stop_reason = "max_calls"
            except Exception as exc:
                stop_reason = "error"
                run_error = str(exc)
            break

    ids = cited_ids(final_answer)
    cited_parents = parent_ids([{"chunk_id": chunk_id} for chunk_id in ids])
    elapsed = time.perf_counter() - started
    row = {
        "qid": qid,
        "stratum": question.get("stratum", "golden"),
        "domain": question["domain"],
        "archetype": question["archetype"],
        "arm": args.arm,
        "model": args.model,
        "found": found,
        "cited": bool(positive.intersection(cited_parents)),
        "first_hit_call": first_hit_call,
        "n_calls": len(calls),
        "invalid_calls": invalid_calls,
        "empty_results": empty_results,
        "gave_up": not bool(final_answer.strip()) or cap_reached,
        "prompt_tokens_total": prompt_total,
        "completion_tokens_total": completion_total,
        "max_prompt_tokens": max_prompt,
        "tool_tokens_total": tool_tokens_total,
        "tokens_to_first_hit": tokens_to_first_hit,
        "cited_ids": ids,
        "final_answer": final_answer or (run_error or ""),
        "stop_reason": stop_reason,
        "turns": turns,
        "wall_s": round(elapsed, 3),
        "calls": calls,
    }
    transcript_dir = ROOT / "data/bench/transcripts" / f"{args.arm}-{args.model}"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    (transcript_dir / f"{qid}.json").write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return row


async def _run(args, questions: list[dict], existing: set[str]) -> None:
    function_tools = await server.mcp.list_tools()
    offered_tools, tools_by_name = _tool_definitions(function_tools)
    client = AsyncOpenAI(base_url=BASE_URL, api_key=_load_api_key())
    todo = [question for question in questions if question["qid"] not in existing]
    semaphore = asyncio.Semaphore(args.concurrency)
    output_path = ROOT / "data/bench/runs" / f"{args.arm}-{args.model}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = 0

    async def worker(question: dict) -> None:
        nonlocal completed
        async with semaphore:
            row = await _run_question(question, args, client, offered_tools, tools_by_name)
            async with WRITE_LOCK:
                with output_path.open("a", encoding="utf-8") as output:
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
            completed += 1
            print(f"[{completed}/{len(todo)}] {question['qid']} stop={row['stop_reason']} calls={row['n_calls']}",
                  file=sys.stderr, flush=True)

    await asyncio.gather(*(worker(question) for question in todo))
    await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--qids", help="Comma-separated question IDs")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-calls", type=int, default=8)
    parser.add_argument("--max-tool-tokens", type=int, default=25000)
    parser.add_argument("--thinking", choices=("off", "on"), default="off")
    args = parser.parse_args()

    os.environ["KB_CALL_LOG"] = f"data/bench/calls/{args.arm}-{args.model}.jsonl"
    (ROOT / "data/bench/calls").mkdir(parents=True, exist_ok=True)
    questions = [json.loads(line) for line in Path(args.questions).read_text(encoding="utf-8").splitlines() if line]
    if args.qids:
        wanted = set(args.qids.split(","))
        questions = [question for question in questions if question["qid"] in wanted]
    if args.limit is not None:
        questions = questions[:args.limit]
    output_path = ROOT / "data/bench/runs" / f"{args.arm}-{args.model}.jsonl"
    existing = set()
    if output_path.exists():
        existing = {json.loads(line)["qid"] for line in output_path.read_text(encoding="utf-8").splitlines() if line}
    asyncio.run(_run(args, questions, existing))


if __name__ == "__main__":
    main()
