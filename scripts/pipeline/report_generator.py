from __future__ import annotations

from typing import Any
import re

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


def _compact_text(text: str, max_len: int = 78) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 1].rstrip() + "…"


def _first_sentence(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if not normalized:
        return ""
    match = re.match(r"^(.+?[。！？.!?])(?:\s|$)", normalized)
    if match:
        return match.group(1).strip()
    return normalized


def _extract_mainlines(clusters: list[dict[str, Any]]) -> list[str]:
    if not clusters:
        return [
            "来源数据不足，今日主线暂不可判定。",
            "优先恢复来源连通性后再做事件级判断。",
        ]

    score_by_category: dict[str, float] = {}
    for cluster in clusters:
        category = str(cluster.get("category", "综合")).strip() or "综合"
        score_by_category[category] = score_by_category.get(category, 0.0) + float(cluster.get("importance", 0.0))

    top_categories = sorted(score_by_category.items(), key=lambda x: x[1], reverse=True)[:2]
    lines = [f"高优先级议题集中在「{category}」方向。" for category, _ in top_categories]
    if len(lines) < 2:
        lines.append("建议优先跟踪多来源交叉验证的高重要性事件。")
    return lines[:2]


def _risk_temperature(clusters: list[dict[str, Any]]) -> str:
    if not clusters:
        return "低"

    avg_importance = sum(float(cluster.get("importance", 0.0)) for cluster in clusters) / max(len(clusters), 1)
    geo_signals = 0
    for cluster in clusters:
        text = " ".join(
            [
                str(cluster.get("category", "")),
                str(cluster.get("subcategory", "")),
                str(cluster.get("event_title", "")),
            ]
        ).lower()
        if any(keyword in text for keyword in ("国际", "地缘", "冲突", "战争", "能源", "航运", "financial", "risk")):
            geo_signals += 1

    if avg_importance >= 8.0 or geo_signals >= 2:
        return "高"
    if avg_importance >= 6.0:
        return "中"
    return "低"


def _build_actions(takeaways: list[str]) -> list[str]:
    defaults = [
        "优先跟踪跨来源一致的高重要事件，减少单源噪声。",
        "对高波动议题设定24小时复盘机制，动态更新判断。",
        "将重点事件映射到行动清单，避免信息过载无执行。",
    ]
    actions: list[str] = []

    for item in takeaways[:3]:
        compact = _compact_text(item, max_len=64)
        if compact and compact not in actions:
            actions.append(compact)

    for item in defaults:
        compact = _compact_text(item, max_len=64)
        if compact not in actions:
            actions.append(compact)
        if len(actions) >= 3:
            break

    return actions[:3]


def _compact_points(items: list[str], fallback: str) -> list[str]:
    if not items:
        return [fallback]
    return [_compact_text(item, max_len=72) for item in items]


def render_report(
    report_date: str,
    clusters: list[EventCluster | dict[str, Any]],
    insights: list[str],
    takeaways: list[str],
    limitations: str,
    stats: dict[str, int],
) -> str:
    normalized_clusters = [_cluster_as_dict(cluster) for cluster in clusters]
    mainlines = _extract_mainlines(normalized_clusters)
    risk_temperature = _risk_temperature(normalized_clusters)
    actions = _build_actions(takeaways)

    lines: list[str] = [
        f"# 新加坡与国际重大新闻日报（{report_date}）",
        "",
        "## 30秒快读",
        f"- 主线1：{mainlines[0]}",
        f"- 主线2：{mainlines[1]}",
        f"- 风险温度：{risk_temperature}",
        f"- 今日行动1：{actions[0]}",
        f"- 今日行动2：{actions[1] if len(actions) > 1 else actions[0]}",
        f"- 今日行动3：{actions[2] if len(actions) > 2 else actions[-1]}",
        "",
        "## 今日执行摘要",
        f"- 原始候选: {stats.get('input_count', 0)}",
        f"- 当日有效候选: {stats.get('today_count', 0)}",
        f"- 去重后事件: {stats.get('deduped_count', 0)}",
        f"- 最终输出: {stats.get('output_count', 0)}",
        "",
        "## Top 5 事件卡片",
    ]

    if not normalized_clusters:
        lines.extend(["", "今日无可输出的高置信事件。"])
    else:
        for idx, data in enumerate(normalized_clusters, start=1):
            category = _compact_text(str(data.get("category", "综合")), max_len=14) or "综合"
            subcategory = _compact_text(str(data.get("subcategory", "综合")), max_len=14) or "综合"
            title = _compact_text(str(data.get("event_title", "未命名事件")), max_len=64) or "未命名事件"
            conclusion = _first_sentence(str(data.get("summary_cn", "")).strip()) or title
            conclusion = _compact_text(conclusion, max_len=72)
            impact = _compact_text(str(data.get("impact_cn", "")).strip() or "暂无影响分析", max_len=72)
            risk_or_op = _compact_text(
                str(data.get("risk_opportunity_cn", "")).strip() or "暂无风险机会分析",
                max_len=72,
            )
            lines.extend(
                [
                    "",
                    f"### #{idx} [{category}/{subcategory}] {title}",
                    f"- 结论：{conclusion}",
                    f"- 影响：{impact}",
                    f"- 风险/机会：{risk_or_op}",
                    f"- 来源：{_render_sources(data.get('source_urls', []))}",
                ]
            )

    lines.extend(["", "## 今日关键 Insights"])
    insight_points = _compact_points(insights, "今日未产出额外洞察。")
    lines.extend([f"- {point}" for point in insight_points])

    lines.extend(["", "## 今日 Takeaways"])
    takeaway_points = _compact_points(takeaways, "今日未产出可执行建议。")
    lines.extend([f"- {point}" for point in takeaway_points])

    lines.extend(
        [
            "",
            "## 数据覆盖与局限说明",
            f"- {_compact_text(limitations or '未检测到明显局限。', max_len=120)}",
        ]
    )

    return "\n".join(lines).strip() + "\n"
