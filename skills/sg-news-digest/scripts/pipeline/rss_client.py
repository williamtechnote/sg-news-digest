from __future__ import annotations

from typing import Any

import feedparser
import requests


DEFAULT_HEADERS = {
    "User-Agent": "sg-news-digest/1.0 (+https://openai.com)",
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
}


def fetch_feed(url: str, timeout: int = 15) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def _extract_summary(entry: dict[str, Any]) -> str:
    summary = entry.get("summary") or entry.get("description")
    if summary:
        return str(summary)

    details = entry.get("summary_detail")
    if isinstance(details, dict):
        value = details.get("value")
        if value:
            return str(value)
    return ""


def _extract_published(entry: dict[str, Any]) -> str:
    for key in ("published", "updated", "pubDate"):
        value = entry.get(key)
        if value:
            return str(value)
    return ""


def parse_feed(xml_text: str) -> list[dict[str, str]]:
    parsed = feedparser.parse(xml_text)
    entries: list[dict[str, str]] = []

    for entry in parsed.entries:
        entries.append(
            {
                "title": str(entry.get("title", "")).strip(),
                "link": str(entry.get("link", "")).strip(),
                "summary": _extract_summary(entry).strip(),
                "published": _extract_published(entry).strip(),
                "language": str(entry.get("language", "")).strip(),
            }
        )
    return entries
