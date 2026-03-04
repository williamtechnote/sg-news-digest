from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
from zoneinfo import ZoneInfo
import re

from dateutil import parser as date_parser

from pipeline.models import NewsItem


_TAG_RE = re.compile(r"<[^>]+>")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub(" ", unescape(text or ""))).strip()


def parse_published_at(raw: str, timezone_name: str = "Asia/Singapore") -> str:
    if not raw:
        dt = datetime.now(timezone.utc)
    else:
        try:
            dt = date_parser.parse(raw)
        except (TypeError, ValueError, OverflowError):
            dt = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(ZoneInfo(timezone_name)).isoformat()


def detect_language(text: str, explicit_language: str = "") -> str:
    if explicit_language:
        return explicit_language.lower()[:5]
    return "zh" if _CJK_RE.search(text or "") else "en"


def is_same_sg_day(iso_time: str, target_date: str, timezone_name: str = "Asia/Singapore") -> bool:
    dt = date_parser.parse(iso_time)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    sg_date = dt.astimezone(ZoneInfo(timezone_name)).date().isoformat()
    return sg_date == target_date


def normalize_entries(raw_items: list[dict[str, str]], timezone_name: str) -> list[NewsItem]:
    normalized: list[NewsItem] = []

    for raw in raw_items:
        title = strip_html(raw.get("title", ""))
        url = raw.get("link", "").strip() or raw.get("url", "").strip()
        if not title or not url:
            continue

        summary = strip_html(raw.get("summary", ""))
        published_at = parse_published_at(raw.get("published", ""), timezone_name)
        language = detect_language(f"{title} {summary}", raw.get("language", ""))
        normalized.append(
            NewsItem(
                source=raw.get("source", "unknown"),
                title=title,
                url=url,
                published_at=published_at,
                summary=summary,
                language=language,
            )
        )
    return normalized


def filter_items_by_date(items: list[NewsItem], target_date: str, timezone_name: str) -> list[NewsItem]:
    return [item for item in items if is_same_sg_day(item.published_at, target_date, timezone_name)]
