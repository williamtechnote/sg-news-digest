from __future__ import annotations

from pipeline.report_generator import render_report


def test_render_report_contains_required_sections() -> None:
    md = render_report(
        report_date="2026-03-04",
        clusters=[],
        insights=["insight1"],
        takeaways=["takeaway1"],
        limitations="none",
        stats={"input_count": 0, "today_count": 0, "deduped_count": 0, "output_count": 0},
    )
    assert "## 30秒快读" in md
    assert "## 今日执行摘要" in md
    assert "## Top 5 事件卡片" in md
    assert "## 今日关键 Insights" in md
    assert "## 今日 Takeaways" in md


def test_render_report_renders_card_fields() -> None:
    clusters = [
        {
            "event_title": "新加坡推出新的公共住房政策并加快配套交付",
            "category": "政策",
            "subcategory": "住房",
            "importance": 8.8,
            "summary_cn": "政府宣布新一轮公共住房供给与配套前置安排，目标是改善新住区入伙初期生活便利度。",
            "impact_cn": "有助于缓解住房供需紧张并改善居民体验。",
            "risk_opportunity_cn": "风险是高密度开发带来的施工与交通压力，机会是土地效率与供给节奏提升。",
            "source_urls": ["https://example.com/a", "https://example.com/b"],
        }
    ]
    md = render_report(
        report_date="2026-03-04",
        clusters=clusters,
        insights=["insight1"],
        takeaways=["takeaway1"],
        limitations="none",
        stats={"input_count": 12, "today_count": 10, "deduped_count": 6, "output_count": 1},
    )

    assert "### #1 [政策/住房] 新加坡推出新的公共住房政策并加快配套交付" in md
    assert "- 结论：" in md
    assert "- 影响：" in md
    assert "- 风险/机会：" in md
    assert "- 来源：" in md
