from __future__ import annotations

from typing import Any

from pipeline.models import EventCluster


def _cluster_as_dict(cluster: EventCluster | dict[str, Any]) -> dict[str, Any]:
    if isinstance(cluster, EventCluster):
        return {
            "event_title": cluster.event_title,
            "category": cluster.category,
            "subcategory": cluster.subcategory,
            "importance": cluster.importance,
            "summary_cn": cluster.summary_cn,
            "impact_cn": cluster.impact_cn,
            "risk_opportunity_cn": cluster.risk_opportunity_cn,
            "source_urls": cluster.source_urls,
            "source_names": cluster.source_names,
            "item_ids": cluster.item_ids,
        }
    return cluster


def _render_sources(urls: list[str]) -> str:
    if not urls:
        return "无可用来源链接"
    rendered = [f"[{idx}]({url})" for idx, url in enumerate(urls[:3], start=1)]
    return " ".join(rendered)


def render_report(
    report_date: str,
    clusters: list[EventCluster | dict[str, Any]],
    insights: list[str],
    takeaways: list[str],
    limitations: str,
    stats: dict[str, int],
) -> str:
    lines: list[str] = [
        f"# 新加坡与国际重大新闻日报（{report_date}）",
        "",
        "## 今日执行摘要",
        f"- 原始候选: {stats.get('input_count', 0)}",
        f"- 当日有效候选: {stats.get('today_count', 0)}",
        f"- 去重后事件: {stats.get('deduped_count', 0)}",
        f"- 最终输出: {stats.get('output_count', 0)}",
        "",
        "## Top 5 新闻详解",
    ]

    if not clusters:
        lines.extend(["", "今日无可输出的高置信事件。"])
    else:
        for idx, cluster in enumerate(clusters, start=1):
            data = _cluster_as_dict(cluster)
            lines.extend(
                [
                    "",
                    f"### {idx}. {data.get('event_title', '未命名事件')}",
                    f"- 分类: {data.get('category', '综合')} / {data.get('subcategory', '综合')}",
                    f"- 重要性: {data.get('importance', 0)}",
                    f"- 摘要: {data.get('summary_cn', '').strip() or '暂无摘要'}",
                    f"- 影响分析: {data.get('impact_cn', '').strip() or '暂无影响分析'}",
                    f"- 风险/机会: {data.get('risk_opportunity_cn', '').strip() or '暂无风险机会分析'}",
                    f"- 来源: {_render_sources(data.get('source_urls', []))}",
                ]
            )

    lines.extend(["", "## 今日关键 Insights"])
    if insights:
        lines.extend([f"- {insight}" for insight in insights])
    else:
        lines.append("- 今日未产出额外洞察。")

    lines.extend(["", "## 今日 Takeaways"])
    if takeaways:
        lines.extend([f"- {takeaway}" for takeaway in takeaways])
    else:
        lines.append("- 今日未产出可执行建议。")

    lines.extend(
        [
            "",
            "## 数据覆盖与局限说明",
            f"- {limitations or '未检测到明显局限。'}",
        ]
    )

    return "\n".join(lines).strip() + "\n"
