from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = ROOT_DIR / "config" / "defaults.env"


@dataclass
class Settings:
    timezone: str
    top_n: int
    request_timeout: int
    request_retries: int
    semantic_timeout: int
    codex_model: str
    source_urls: dict[str, str]


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _as_int(raw: str, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def load_settings(env_file: Path | None = None, overrides: dict[str, str] | None = None) -> Settings:
    values: dict[str, str] = {}
    values.update(_read_env_file(env_file or DEFAULT_ENV_FILE))
    values.update({k: v for k, v in os.environ.items() if isinstance(v, str)})
    if overrides:
        values.update(overrides)

    source_urls = {
        "google_news": values.get("GOOGLE_NEWS_RSS", "").strip(),
        "cna": values.get("CNA_RSS", "").strip(),
        "straits_times": values.get("ST_RSS", "").strip(),
        "zaobao": values.get("ZAOBAO_RSS", "").strip(),
    }

    return Settings(
        timezone=values.get("TIMEZONE", "Asia/Singapore"),
        top_n=_as_int(values.get("TOP_N", "5"), 5),
        request_timeout=_as_int(values.get("REQUEST_TIMEOUT", "15"), 15),
        request_retries=_as_int(values.get("REQUEST_RETRIES", "2"), 2),
        semantic_timeout=_as_int(values.get("SEMANTIC_TIMEOUT", "240"), 240),
        codex_model=values.get("CODEX_MODEL", "").strip(),
        source_urls=source_urls,
    )
