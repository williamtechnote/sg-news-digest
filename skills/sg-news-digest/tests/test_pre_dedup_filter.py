from __future__ import annotations

from pipeline.pre_dedup_filter import dedup_titles, dedup_urls


def test_dedup_urls_removes_duplicates() -> None:
    items = [{"url": "https://a"}, {"url": "https://a"}, {"url": "https://b"}]
    output = dedup_urls(items)
    assert len(output) == 2


def test_dedup_titles_collapses_near_identical_titles() -> None:
    items = [
        {"title": "MAS keeps policy unchanged"},
        {"title": "MAS keeps policy unchanged!"},
        {"title": "US Fed signals pause"},
    ]
    output = dedup_titles(items)
    assert len(output) == 2
