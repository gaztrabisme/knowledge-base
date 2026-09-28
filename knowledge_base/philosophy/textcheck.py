"""Measure Chinese PDF extraction against vendored common-character sets."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from ..config import ROOT

_CJK_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0x20000, 0x2FA1F))
MAX_OUTSIDE_SHARE = 0.10
MAX_PEER_GAP = 0.20


@dataclass(frozen=True)
class TextCheck:
    lang: str
    cjk_count: int
    outside_count: int
    outside_share: float
    passed: bool
    threshold: float = MAX_OUTSIDE_SHARE
    comparison: dict | None = None
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return any(start <= code <= end for start, end in _CJK_RANGES)


@lru_cache(maxsize=2)
def common_characters(lang: str) -> frozenset[str]:
    suffix = "hant" if lang.casefold() in {"zh-hant", "zh-tw", "big5"} else "hans"
    path = ROOT / "data" / "philosophy" / f"chinese_common_{suffix}.txt"
    return frozenset(char for char in path.read_text(encoding="utf-8") if _is_cjk(char))


def check_text(text: str, lang: str) -> TextCheck:
    """Return the outside-common-character share for extracted text."""
    if not lang.casefold().startswith("zh") and lang.casefold() not in {"gb", "big5"}:
        return TextCheck(lang, 0, 0, 0.0, True, reason="not a Chinese-language edition")
    chars = [char for char in text if _is_cjk(char)]
    if not chars:
        return TextCheck(lang, 0, 0, 1.0, False, reason="no extractable CJK characters")
    common = common_characters(lang)
    outside = sum(char not in common for char in chars)
    share = outside / len(chars)
    passed = share < MAX_OUTSIDE_SHARE
    reason = "within common-character threshold" if passed else "outside-common-character share exceeds 10%"
    return TextCheck(lang, len(chars), outside, share, passed, reason=reason)


def check_pdf(path: str | Path, lang: str) -> TextCheck:
    """Extract a PDF with PyMuPDF and measure every page."""
    import pymupdf

    with pymupdf.open(str(path)) as document:
        text = "\n".join(page.get_text("text") for page in document)
    return check_text(text, lang)


def compare_editions(checks: Mapping[str, TextCheck]) -> dict[str, TextCheck]:
    """Compare each edition only with other clean candidates in its script group."""
    result = {}
    for name, item in checks.items():
        clean_peers = [
            other.outside_share for peer_name, other in checks.items()
            if peer_name != name and other.cjk_count and other.passed
        ]
        if not clean_peers:
            result[name] = replace(item, comparison={
                "peer_count": 0,
                "note": "no other passing candidate in this script group",
            })
            continue
        median = statistics.median(clean_peers)
        if not item.cjk_count:
            result[name] = replace(item, comparison={"peer_count": len(clean_peers), "peer_median": median})
            continue
        peer_failed = item.outside_share > median + MAX_PEER_GAP
        passed = item.passed and not peer_failed
        reason = item.reason
        if peer_failed:
            reason = f"outside share is {item.outside_share:.2%}, over peer median {median:.2%} by more than 20 points"
        result[name] = replace(
            item, passed=passed,
            comparison={"peer_count": len(clean_peers), "peer_median": median, "max_peer_gap": MAX_PEER_GAP},
            reason=reason,
        )
    return result
