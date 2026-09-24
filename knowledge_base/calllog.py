"""Optional JSONL logging for calls to the knowledge-base tools."""

import contextvars
import functools
import inspect
import json
import os
import re
import threading
import time
from datetime import datetime, timezone


_run_id = contextvars.ContextVar("kb_call_log_run_id", default=None)
_write_lock = threading.Lock()
_CHUNK_ID = re.compile(r"^(.+)-p(\d+)-c\d+$")
_TOKEN_ENCODER = None


def set_run_id(value: str | None) -> None:
    """Set the run identifier attached to subsequent calls in this context."""
    _run_id.set(value)


def _token_count(value: object) -> int:
    global _TOKEN_ENCODER
    if _TOKEN_ENCODER is None:
        import tiktoken

        _TOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")
    serialized = json.dumps(value)
    return len(_TOKEN_ENCODER.encode(serialized))


def _ids(value: object) -> tuple[list[str], list[str]]:
    chunk_ids: list[str] = []
    parent_ids: list[str] = []

    def add(items: list[str], item: object) -> None:
        if isinstance(item, str) and item and item not in items:
            items.append(item)

    def visit(item: object) -> None:
        if isinstance(item, dict):
            add(chunk_ids, item.get("chunk_id"))
            add(parent_ids, item.get("parent_id"))
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(value)
    for chunk_id in chunk_ids:
        match = _CHUNK_ID.match(chunk_id)
        if match:
            add(parent_ids, f"{match.group(1)}-p{match.group(2)}")
    return chunk_ids, parent_ids


def _result_count(value: object) -> int:
    if isinstance(value, dict) and isinstance(value.get("results"), list):
        return len(value["results"])
    if isinstance(value, (list, tuple)):
        return len(value)
    return int(value is not None and value != "")


def _result_error(result: object) -> str | None:
    if isinstance(result, str) and "not found" in result.lower():
        return result
    errors: list[str] = []

    def visit(item: object) -> None:
        if isinstance(item, dict):
            if "error" in item:
                errors.append(str(item["error"]))
            for child in item.values():
                if isinstance(child, (dict, list, tuple)):
                    visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(result)
    return "; ".join(dict.fromkeys(errors)) or None


def _append(path: str, function, args: tuple, kwargs: dict, result: object,
            error: str | None, latency_s: float) -> None:
    try:
        bound = inspect.signature(function).bind_partial(*args, **kwargs)
        chunk_ids, parent_ids = _ids(result)
        n_results = _result_count(result)
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": _run_id.get(),
            "tool": function.__name__,
            "args": bound.arguments,
            "error": error if error is not None else _result_error(result),
            "n_results": n_results,
            "tokens": _token_count(result),
            "chunk_ids": chunk_ids,
            "parent_ids": parent_ids,
            "latency_s": latency_s,
        }
        line = json.dumps(row, ensure_ascii=False, default=str)
        with _write_lock, open(path, "a", encoding="utf-8") as output:
            output.write(line + "\n")
    except Exception:
        # Logging is observational: an unavailable log must not change tool behavior.
        return


def logged(function):
    """Log a tool call to ``KB_CALL_LOG`` when that environment variable is set."""
    if inspect.iscoroutinefunction(function):
        @functools.wraps(function)
        async def async_wrapper(*args, **kwargs):
            path = os.environ.get("KB_CALL_LOG")
            if not path:
                return await function(*args, **kwargs)
            started = time.perf_counter()
            try:
                result = await function(*args, **kwargs)
            except Exception as exc:
                _append(path, function, args, kwargs, None, str(exc), time.perf_counter() - started)
                raise
            _append(path, function, args, kwargs, result, None, time.perf_counter() - started)
            return result

        return async_wrapper

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        path = os.environ.get("KB_CALL_LOG")
        if not path:
            return function(*args, **kwargs)
        started = time.perf_counter()
        try:
            result = function(*args, **kwargs)
        except Exception as exc:
            _append(path, function, args, kwargs, None, str(exc), time.perf_counter() - started)
            raise
        _append(path, function, args, kwargs, result, None, time.perf_counter() - started)
        return result

    return wrapper
