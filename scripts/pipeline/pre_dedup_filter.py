from __future__ import annotations

from dataclasses import replace
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pipeline.models import NewsItem


_TRACKING_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "ocid",
}

_SG_KEYWORDS = {
    "singapore",
    "sg",
    "hdb",
    "mas",
    "moh",
    "mti",
    "parliament",
    "cna",
    "straits",
}

_GLOBAL_MAJOR_KEYWORDS = {
    "fed",
    "federal reserve",
    "china",
    "us",
    "eu",
    "ukraine",
    "gaza",
    "oil",
    "inflation",
    "tariff",
    "war",
    "ceasefire",
    "nato",
    "election",
}


def normalize_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    clean_query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in _TRACKING_KEYS]
    clean = parsed._replace(query=urlencode(clean_query, doseq=True), fragment="")
    return urlunparse(clean)


def dedup_urls(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []

    for item in items:
        raw = str(item.get("url", "") or item.get("link", "")).strip()
        if not raw:
            continue
        normalized = normalize_url(raw)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(item)
    return result


def _title_fingerprint(title: str) -> str:
    lowered = (title or "").lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lowered)


def dedup_titles(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []

    for item in items:
        fingerprint = _title_fingerprint(str(item.get("title", "")))
        if not fingerprint:
            continue
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        result.append(item)
    return result


def dedup_news_items(items: list[NewsItem]) -> list[NewsItem]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    output: list[NewsItem] = []

    for item in items:
        normalized = normalize_url(item.url)
        fingerprint = _title_fingerprint(item.title)

        if normalized in seen_urls or fingerprint in seen_titles:
            continue

        seen_urls.add(normalized)
        seen_titles.add(fingerprint)
        output.append(replace(item, normalized_url=normalized))
    return output


def filter_scope(items: list[NewsItem]) -> list[NewsItem]:
    scoped: list[NewsItem] = []
    for item in items:
        text = f"{item.title} {item.summary}".lower()
        if any(keyword in text for keyword in _SG_KEYWORDS):
            scoped.append(item)
            continue
        if any(keyword in text for keyword in _GLOBAL_MAJOR_KEYWORDS):
            scoped.append(item)

    # Avoid over-pruning due to imperfect keyword matching.
    return scoped if scoped else items
