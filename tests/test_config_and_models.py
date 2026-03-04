from __future__ import annotations

from pipeline.config import load_settings
from pipeline.models import NewsItem


def test_load_settings_top_n_default_to_5() -> None:
    settings = load_settings(overrides={"TOP_N": "5"})
    assert settings.top_n == 5


def test_news_item_required_fields() -> None:
    item = NewsItem(
        source="cna",
        title="Sample",
        url="https://example.com",
        published_at="2026-03-04T08:00:00+08:00",
        summary="summary",
        language="en",
    )
    assert item.source == "cna"
