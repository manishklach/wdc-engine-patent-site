from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    default_admission_window_ms: int = int(os.getenv("DEFAULT_ADMISSION_WINDOW_MS", "900"))
    sql_admission_window_ms: int = int(os.getenv("SQL_ADMISSION_WINDOW_MS", "900"))
    nl_admission_window_ms: int = int(os.getenv("NL_ADMISSION_WINDOW_MS", "1200"))
    api_admission_window_ms: int = int(os.getenv("API_ADMISSION_WINDOW_MS", "750"))
    nl_similarity_threshold: float = float(os.getenv("NL_SIMILARITY_THRESHOLD", "0.78"))
    sentence_transformer_model: str = os.getenv(
        "SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    def admission_window_for(self, task_type: str) -> int:
        mapping = {
            "SQL_QUERY": self.sql_admission_window_ms,
            "NATURAL_LANGUAGE": self.nl_admission_window_ms,
            "API_CALL": self.api_admission_window_ms,
        }
        return mapping.get(task_type, self.default_admission_window_ms)


settings = Settings()
