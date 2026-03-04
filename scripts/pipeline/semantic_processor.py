from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import subprocess
import tempfile

from dateutil import parser as date_parser
from zoneinfo import ZoneInfo

from pipeline.models import EventCluster, NewsItem, SemanticResult


def build_prompt(items: list[dict], top_n: int, report_date: str) -> str:
    instruction = {
        "role": "system",
        "task": "新闻语义聚类、去重、分类与决策分析",
        "constraints": {
            "language": "中文",
            "max_items": top_n,
            "date": report_date,
            "scope": "新加坡与国际重大新闻",
        },
    }

    return (
        "你是新闻分析助手。请对输入新闻做语义去重，输出 Top "
        f"{top_n} 事件，语言为中文。\n"
        "每个事件必须包含：event_title/category/subcategory/importance/summary_cn/"
        "impact_cn/risk_opportunity_cn/source_urls/source_names/item_ids。\n"
        f"元信息: {json.dumps(instruction, ensure_ascii=False)}\n"
        f"输入JSON:\n{json.dumps(items, ensure_ascii=False)}"
    )


def _schema_default_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "event_clusters.schema.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _invoke_codex(
    payload: list[dict],
    top_n: int,
    report_date: str,
    schema_path: Path,
    timeout_sec: int,
    model: str,
) -> dict:
    with tempfile.TemporaryDirectory(prefix="sg_digest_semantic_") as tmp_dir:
        output_path = Path(tmp_dir) / "semantic_output.json"
        prompt = build_prompt(payload, top_n=top_n, report_date=report_date)
        cmd = [
            "codex",
            "exec",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
        ]
        if model:
            cmd.extend(["-m", model])
        # Use stdin instead of argv to avoid command-length and escaping failures.
        cmd.append("-")

        proc = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            input=prompt,
        )
        # output file is authoritative; fallback to stdout only if file missing
        if output_path.exists():
            return _load_json(output_path)
        return json.loads(proc.stdout)


def _infer_category(text: str) -> tuple[str, str]:
    lowered = text.lower()
    mapping = [
        ("政策治理", "政策", ["policy", "parliament", "government", "ministry", "regulation", "law"]),
        ("经济金融", "宏观", ["inflation", "gdp", "mas", "rate", "economy", "bond", "fed"]),
        ("商业产业", "企业", ["company", "earnings", "startup", "merger", "trade"]),
        ("科技创新", "科技", ["ai", "chip", "cyber", "data", "technology"]),
        ("国际局势", "地缘", ["war", "ceasefire", "tariff", "sanction", "election", "nato", "china", "us"]),
        ("社会民生", "社会", ["health", "housing", "education", "crime", "transport"]),
    ]

    for category, subcategory, keywords in mapping:
        if any(keyword in lowered for keyword in keywords):
            return category, subcategory
    return "综合", "综合"


def _freshness_score(iso_time: str) -> float:
    try:
        dt = date_parser.parse(iso_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        now = datetime.now(ZoneInfo("Asia/Singapore"))
        hours = max((now - dt.astimezone(ZoneInfo("Asia/Singapore"))).total_seconds() / 3600, 0)
        if hours <= 3:
            return 3.0
        if hours <= 8:
            return 2.0
        if hours <= 18:
            return 1.0
    except Exception:  # noqa: BLE001
        pass
    return 0.5


def fallback_semantic(items: list[NewsItem], top_n: int, report_date: str, reason: str = "") -> SemanticResult:
    clusters: list[EventCluster] = []
    grouped: dict[str, list[NewsItem]] = {}

    for item in items:
        key = item.title.lower().strip()
        grouped.setdefault(key, []).append(item)

    for _, group in grouped.items():
        rep = group[0]
        category, subcategory = _infer_category(f"{rep.title} {rep.summary}")
        importance = min(10.0, len(group) * 1.5 + _freshness_score(rep.published_at))
        urls = sorted({item.normalized_url or item.url for item in group})
        sources = sorted({item.source for item in group})
        summary = rep.summary or rep.title

        clusters.append(
            EventCluster(
                event_title=rep.title,
                category=category,
                subcategory=subcategory,
                importance=importance,
                summary_cn=summary,
                impact_cn="该事件可能影响相关政策预期、市场风险偏好与行业资源分配。",
                risk_opportunity_cn="建议跟踪后续官方披露与跨媒体一致性信号，识别潜在风险与配置机会。",
                source_urls=urls,
                source_names=sources,
                item_ids=[item.item_id for item in group],
            )
        )

    clusters = sorted(clusters, key=lambda x: x.importance, reverse=True)[:top_n]

    if not clusters:
        insights = [f"{report_date} 可用公开新闻不足，暂无可聚类的高置信事件。"]
        takeaways = ["保持来源连通性监控，优先修复抓取失败的新闻源。"]
    else:
        top_category = max(
            ((cluster.category, cluster.importance) for cluster in clusters),
            key=lambda item: item[1],
        )[0]
        cross_source = sum(1 for cluster in clusters if len(cluster.source_names) > 1)
        insights = [
            f"今日 Top {len(clusters)} 事件重心偏向“{top_category}”。",
            f"其中 {cross_source} 条事件获得多来源交叉覆盖，结论置信度相对更高。",
        ]
        takeaways = [
            "优先关注多源共同报道的高重要性事件，降低单源噪声影响。",
            "对高不确定事件建立 24 小时再评估机制，避免一次性决策。",
        ]

    return SemanticResult(
        clusters=clusters,
        insights=insights,
        takeaways=takeaways,
        degraded=True,
        error=reason,
    )


def _parse_clusters(raw: dict, top_n: int) -> tuple[list[EventCluster], list[str], list[str]]:
    raw_clusters = raw.get("clusters") or []
    raw_insights = raw.get("insights") or []
    raw_takeaways = raw.get("takeaways") or []

    clusters: list[EventCluster] = []
    for cluster in raw_clusters[:top_n]:
        clusters.append(
            EventCluster(
                event_title=str(cluster.get("event_title", "")).strip() or "未命名事件",
                category=str(cluster.get("category", "综合")).strip() or "综合",
                subcategory=str(cluster.get("subcategory", "综合")).strip() or "综合",
                importance=float(cluster.get("importance", 0.0)),
                summary_cn=str(cluster.get("summary_cn", "")).strip(),
                impact_cn=str(cluster.get("impact_cn", "")).strip(),
                risk_opportunity_cn=str(cluster.get("risk_opportunity_cn", "")).strip(),
                source_urls=[str(url) for url in cluster.get("source_urls", []) if str(url)],
                source_names=[str(name) for name in cluster.get("source_names", []) if str(name)],
                item_ids=[str(item_id) for item_id in cluster.get("item_ids", []) if str(item_id)],
            )
        )

    insights = [str(x).strip() for x in raw_insights if str(x).strip()]
    takeaways = [str(x).strip() for x in raw_takeaways if str(x).strip()]
    return clusters, insights, takeaways


def semantic_cluster(items: list[NewsItem], top_n: int, report_date: str, settings) -> SemanticResult:
    if not items:
        return SemanticResult(clusters=[], insights=[], takeaways=[], degraded=False)

    payload = [item.to_payload() for item in items]
    schema_path = _schema_default_path()

    try:
        raw = _invoke_codex(
            payload=payload,
            top_n=top_n,
            report_date=report_date,
            schema_path=schema_path,
            timeout_sec=settings.semantic_timeout,
            model=settings.codex_model,
        )
        clusters, insights, takeaways = _parse_clusters(raw, top_n)
        if not clusters:
            return fallback_semantic(items, top_n, report_date, reason="AI 输出为空，回退规则模式")

        if not insights:
            insights = ["今日事件已完成语义聚类，建议重点跟踪高重要性且多源一致事件。"]
        if not takeaways:
            takeaways = ["围绕 Top 事件建立后续追踪与风险预案。"]
        return SemanticResult(clusters=clusters, insights=insights, takeaways=takeaways, degraded=False)
    except Exception as exc:  # noqa: BLE001
        return fallback_semantic(items, top_n, report_date, reason=str(exc))
