from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any


@dataclass
class NewsItem:
    source: str
    title: str
    url: str
    published_at: str
    summary: str
    language: str
    normalized_url: str = ""
    fetched_at: str = ""
    item_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.item_id:
            seed = "|".join([self.source, self.url, self.title, self.published_at])
            self.item_id = sha1(seed.encode("utf-8")).hexdigest()[:16]

    def to_payload(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "summary": self.summary,
            "language": self.language,
        }


@dataclass
class EventCluster:
    event_title: str
    category: str
    subcategory: str
    importance: float
    summary_cn: str
    impact_cn: str
    risk_opportunity_cn: str
    source_urls: list[str]
    source_names: list[str]
    item_ids: list[str]


@dataclass
class SemanticResult:
    clusters: list[EventCluster]
    insights: list[str]
    takeaways: list[str]
    degraded: bool = False
    error: str = ""
