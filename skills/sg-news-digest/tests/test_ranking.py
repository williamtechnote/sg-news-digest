from __future__ import annotations

from pipeline.ranking import select_top_clusters


def test_select_top_clusters_limits_count() -> None:
    clusters = [{"importance": i} for i in range(10)]
    result = select_top_clusters(clusters, top_n=5)
    assert len(result) == 5
    assert result[0]["importance"] == 9
