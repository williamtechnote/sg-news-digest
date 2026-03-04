from __future__ import annotations

from pipeline.models import EventCluster


def select_top_clusters(clusters: list[EventCluster | dict], top_n: int = 5) -> list[EventCluster | dict]:
    def _score(cluster: EventCluster | dict) -> tuple[float, int]:
        if isinstance(cluster, dict):
            importance = float(cluster.get("importance", 0.0))
            sources = len(cluster.get("source_names", []))
            return importance, sources

        return float(cluster.importance), len(cluster.source_names)

    ordered = sorted(clusters, key=_score, reverse=True)
    return ordered[:top_n]
