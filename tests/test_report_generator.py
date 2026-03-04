from __future__ import annotations

from pipeline.report_generator import render_report


def test_render_report_contains_required_sections() -> None:
    md = render_report(
        report_date="2026-03-04",
        clusters=[],
        insights=["insight1"],
        takeaways=["takeaway1"],
        limitations="none",
        stats={"input_count": 0, "output_count": 0},
    )
    assert "## 今日执行摘要" in md
    assert "## 今日关键 Insights" in md
    assert "## 今日 Takeaways" in md
