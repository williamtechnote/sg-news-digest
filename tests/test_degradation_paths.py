from __future__ import annotations

from pipeline.runner import build_limitations_text


def test_limitations_mentions_source_failure() -> None:
    text = build_limitations_text(
        failed_sources=["cna"],
        degraded=True,
        count=3,
        target=5,
    )
    assert "来源受限" in text
    assert "cna" in text.lower()
