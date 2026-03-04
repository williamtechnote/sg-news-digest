from __future__ import annotations

from typing import Callable

from pipeline.config import Settings
from pipeline.rss_client import fetch_feed, parse_feed


_SOURCE_ORDER = ["google_news", "cna", "straits_times", "zaobao"]


def list_enabled_sources() -> list[str]:
    return _SOURCE_ORDER.copy()


def _fetch_with_retry(url: str, timeout: int, retries: int, fetcher: Callable[[str, int], str]) -> str:
    last_error: Exception | None = None
    attempts = retries + 1
    for _ in range(attempts):
        try:
            return fetcher(url, timeout)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("fetch retry loop ended unexpectedly")


def fetch_all_sources(settings: Settings) -> tuple[list[dict[str, str]], list[str]]:
    all_entries: list[dict[str, str]] = []
    failed_sources: list[str] = []

    for source_name in _SOURCE_ORDER:
        url = settings.source_urls.get(source_name, "").strip()
        if not url:
            failed_sources.append(source_name)
            continue

        try:
            xml = _fetch_with_retry(url, settings.request_timeout, settings.request_retries, fetch_feed)
            entries = parse_feed(xml)
        except Exception:  # noqa: BLE001
            failed_sources.append(source_name)
            continue

        for entry in entries:
            enriched = dict(entry)
            enriched["source"] = source_name
            enriched.setdefault("url", entry.get("link", ""))
            all_entries.append(enriched)

    return all_entries, failed_sources
