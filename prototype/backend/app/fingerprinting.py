from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings
from .models import FingerprintRecord, TaskType

WHITESPACE_RE = re.compile(r"\s+")
STRING_LITERAL_RE = re.compile(r"'([^']*)'")
NUMBER_LITERAL_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
FROM_JOIN_ALIAS_RE = re.compile(r"\b(from|join)\s+([a-zA-Z_][\w.]*)\s+(?:as\s+)?([a-zA-Z_]\w*)", re.IGNORECASE)
ALIAS_REF_TEMPLATE = r"\b{alias}\."


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_sql(sql: str) -> str:
    canonical = _normalize_whitespace(sql.lower())
    canonical = re.sub(r"--.*?$", "", canonical, flags=re.MULTILINE)
    canonical = re.sub(r"/\*.*?\*/", "", canonical, flags=re.DOTALL)

    alias_map: dict[str, str] = {}
    alias_index = 1
    for match in FROM_JOIN_ALIAS_RE.finditer(canonical):
        alias = match.group(3)
        if alias not in alias_map:
            alias_map[alias] = f"t{alias_index}"
            alias_index += 1

    for source_alias, target_alias in alias_map.items():
        canonical = re.sub(ALIAS_REF_TEMPLATE.format(alias=re.escape(source_alias)), f"{target_alias}.", canonical)
        canonical = re.sub(rf"\bas\s+{re.escape(source_alias)}\b", f"as {target_alias}", canonical)
        canonical = re.sub(
            rf"\b(from|join)\s+([a-zA-Z_][\w.]*)\s+{re.escape(source_alias)}\b",
            lambda match: f"{match.group(1)} {match.group(2)} {target_alias}",
            canonical,
        )

    string_index = 1

    def replace_string(_: re.Match[str]) -> str:
        nonlocal string_index
        token = f":STR_{string_index}"
        string_index += 1
        return token

    number_index = 1

    def replace_number(_: re.Match[str]) -> str:
        nonlocal number_index
        token = f":NUM_{number_index}"
        number_index += 1
        return token

    canonical = STRING_LITERAL_RE.sub(replace_string, canonical)
    canonical = NUMBER_LITERAL_RE.sub(replace_number, canonical)
    canonical = canonical.replace('"', "")
    return _normalize_whitespace(canonical)


def canonicalize_api(payload: str) -> str:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return _normalize_whitespace(payload.lower())

    method = str(data.get("method", "GET")).upper()
    endpoint = str(data.get("endpoint", "/")).lower()
    headers = {
        key.lower(): value
        for key, value in dict(data.get("headers", {})).items()
        if key.lower() in {"accept", "content-type"}
    }
    body = data.get("body", {})
    canonical = {
        "method": method,
        "endpoint": endpoint,
        "headers": dict(sorted(headers.items())),
        "body": body,
    }
    return json.dumps(canonical, sort_keys=True)


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.sentence_transformer_model)


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    model = _model()
    embeddings = model.encode(list(texts), normalize_embeddings=True)
    return np.asarray(embeddings)


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right))


def fingerprint_task(task_type: TaskType, payload: str) -> FingerprintRecord:
    if task_type == TaskType.SQL_QUERY:
        canonical = normalize_sql(payload)
        return FingerprintRecord(task_type=task_type, canonical=canonical, exact_hash=_sha256(canonical))

    if task_type == TaskType.API_CALL:
        canonical = canonicalize_api(payload)
        return FingerprintRecord(task_type=task_type, canonical=canonical, exact_hash=_sha256(canonical))

    canonical = _normalize_whitespace(payload)
    embedding = embed_texts([canonical])[0].tolist()
    return FingerprintRecord(
        task_type=task_type,
        canonical=canonical,
        exact_hash=_sha256(canonical.lower()),
        embedding=embedding,
    )
