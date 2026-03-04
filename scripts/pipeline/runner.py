from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import sys

from zoneinfo import ZoneInfo

from pipeline.config import load_settings
from pipeline.normalize import filter_items_by_date, normalize_entries
from pipeline.pre_dedup_filter import dedup_news_items, filter_scope
from pipeline.ranking import select_top_clusters
from pipeline.report_generator import render_report
from pipeline.semantic_processor import fallback_semantic, semantic_cluster
from pipeline.source_fetcher import fetch_all_sources


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SG + international Top News digest")
    parser.add_argument("--date", help="Target date in YYYY-MM-DD (Asia/Singapore)", default=None)
    parser.add_argument("--top", help="Top N events to output", default=5, type=int)
    parser.add_argument("--env-file", help="Path to env file", default=None)
    parser.add_argument("--no-ai", action="store_true", help="Disable Codex semantic clustering and use fallback")
    return parser.parse_args(argv)


def build_limitations_text(
    failed_sources: list[str],
    degraded: bool,
    count: int,
    target: int,
) -> str:
    parts: list[str] = []
    if failed_sources:
        parts.append(f"来源受限: {', '.join(failed_sources)}")
    if degraded:
        parts.append("AI语义处理降级为规则模式")
    if count < target:
        parts.append(f"当日有效事件不足{target}条，实际输出{count}条")

    return "；".join(parts) if parts else "未检测到关键局限。"


def _today_in_timezone(timezone_name: str) -> str:
    return datetime.now(ZoneInfo(timezone_name)).date().isoformat()


def _log(stats: dict) -> None:
    print(json.dumps(stats, ensure_ascii=False), file=sys.stderr)


def run(args: argparse.Namespace) -> int:
    overrides = {"TOP_N": str(args.top)}
    env_file = Path(args.env_file) if args.env_file else None
    settings = load_settings(env_file=env_file, overrides=overrides)

    report_date = args.date or _today_in_timezone(settings.timezone)

    raw_entries, failed_sources = fetch_all_sources(settings)
    normalized = normalize_entries(raw_entries, settings.timezone)
    same_day = filter_items_by_date(normalized, report_date, settings.timezone)
    scoped = filter_scope(same_day)
    deduped = dedup_news_items(scoped)

    if args.no_ai:
        semantic = fallback_semantic(deduped, settings.top_n, report_date, reason="--no-ai enabled")
    else:
        semantic = semantic_cluster(deduped, settings.top_n, report_date, settings)

    top_clusters = select_top_clusters(semantic.clusters, settings.top_n)
    limitations = build_limitations_text(
        failed_sources=failed_sources,
        degraded=semantic.degraded,
        count=len(top_clusters),
        target=settings.top_n,
    )

    stats = {
        "input_count": len(raw_entries),
        "normalized_count": len(normalized),
        "today_count": len(same_day),
        "scoped_count": len(scoped),
        "deduped_count": len(deduped),
        "output_count": len(top_clusters),
        "failed_source_count": len(failed_sources),
        "degraded": semantic.degraded,
    }

    report = render_report(
        report_date=report_date,
        clusters=top_clusters,
        insights=semantic.insights,
        takeaways=semantic.takeaways,
        limitations=limitations,
        stats=stats,
    )
    print(report, end="")

    _log(
        {
            "status": "ok" if top_clusters else "partial",
            "report_date": report_date,
            "failed_sources": failed_sources,
            "degraded": semantic.degraded,
            "semantic_error": semantic.error,
            **stats,
        }
    )

    if not top_clusters:
        return 2
    if semantic.degraded:
        return 2
    return 0


def main() -> int:
    args = parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
