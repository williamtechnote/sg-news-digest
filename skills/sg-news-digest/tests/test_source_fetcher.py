from __future__ import annotations

from pipeline.source_fetcher import list_enabled_sources


def test_list_enabled_sources_returns_four_sources_by_default() -> None:
    names = list_enabled_sources()
    assert set(names) == {"google_news", "cna", "straits_times", "zaobao"}
