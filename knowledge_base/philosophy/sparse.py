"""Small multilingual sparse tokenizer for Latin, Vietnamese, and CJK text."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter

try:
    from opencc import OpenCC
except ImportError as exc:
    raise RuntimeError(
        "Philosophy sparse tokenization requires opencc-python-reimplemented for "
        "Traditional/Simplified Chinese normalization."
    ) from exc

from qdrant_client import models

_TOKEN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]+|[^\W\d_]+", re.UNICODE)
_T2S = OpenCC("t2s")


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return (0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF
            or 0x20000 <= code <= 0x2FA1F)


def tokenize(text: str) -> list[str]:
    """Return lowercased words or CJK unigrams and adjacent bigrams."""
    tokens: list[str] = []
    simplified = _T2S.convert(text)
    normalized = unicodedata.normalize("NFC", simplified).casefold()
    for match in _TOKEN_RE.finditer(normalized):
        run = match.group(0)
        if _is_cjk(run[0]):
            tokens.extend(run)
            tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
        else:
            tokens.append(run)
    return tokens


def _hash(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest(), "big") & 0x7FFFFFFF


def text_to_sparse_vector(text: str) -> models.SparseVector:
    """Hash term frequencies into a deterministic Qdrant sparse vector."""
    counts: Counter[int] = Counter(_hash(token) for token in tokenize(text))
    indices = sorted(counts)
    return models.SparseVector(indices=indices, values=[float(counts[i]) for i in indices])
