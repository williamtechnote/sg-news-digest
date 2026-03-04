# SG News Digest Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Codex skill that fetches daily news from Google News, The Straits Times, CNA, and 联合早报 via official/public RSS or APIs, semantically deduplicates and classifies events, and outputs a Chinese Top 5 Markdown digest with insights and takeaways.

**Architecture:** Use a single Python pipeline with modular stages: source ingest, normalization, pre-dedup filtering, Codex-powered semantic clustering, ranking/selecting Top 5, and Markdown rendering. The runtime entrypoint prints report content to stdout and structured logs to stderr so OpenClaw can schedule and forward output to Telegram.

**Tech Stack:** Python 3.11+, pytest, requests/feedparser, zoneinfo/dateutil, dataclasses or pydantic, shell entrypoint (`run.sh`), Codex CLI (`codex exec`).

---

## Required Skill References During Execution

- `@superpowers/test-driven-development` before each implementation change.
- `@superpowers/systematic-debugging` if any test or runtime behavior is unexpected.
- `@superpowers/verification-before-completion` before claiming done.

### Task 1: Scaffold skill package and test harness

**Files:**
- Create: `skills/sg-news-digest/SKILL.md`
- Create: `skills/sg-news-digest/scripts/run.sh`
- Create: `skills/sg-news-digest/scripts/pipeline/__init__.py`
- Create: `skills/sg-news-digest/tests/test_smoke.py`
- Create: `skills/sg-news-digest/pyproject.toml`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_smoke.py
from pathlib import Path


def test_skill_layout_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "SKILL.md").exists()
    assert (root / "scripts" / "run.sh").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_smoke.py -v`
Expected: FAIL because files do not exist yet.

**Step 3: Write minimal implementation**

```bash
mkdir -p skills/sg-news-digest/scripts/pipeline skills/sg-news-digest/tests
touch skills/sg-news-digest/SKILL.md
printf '#!/usr/bin/env bash\nset -euo pipefail\n' > skills/sg-news-digest/scripts/run.sh
chmod +x skills/sg-news-digest/scripts/run.sh
touch skills/sg-news-digest/scripts/pipeline/__init__.py
printf '[project]\nname = "sg-news-digest"\nversion = "0.1.0"\n' > skills/sg-news-digest/pyproject.toml
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_smoke.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest
git commit -m "chore: scaffold sg-news-digest skill structure"
```

### Task 2: Define config and domain models

**Files:**
- Create: `skills/sg-news-digest/config/defaults.env`
- Create: `skills/sg-news-digest/scripts/pipeline/models.py`
- Create: `skills/sg-news-digest/scripts/pipeline/config.py`
- Test: `skills/sg-news-digest/tests/test_config_and_models.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_config_and_models.py
from skills.sg_news_digest.scripts.pipeline.models import NewsItem


def test_news_item_requires_required_fields():
    item = NewsItem(
        source="cna",
        title="Sample",
        url="https://example.com",
        published_at="2026-03-04T08:00:00+08:00",
        summary="x",
        language="en",
    )
    assert item.source == "cna"
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_config_and_models.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing model.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/models.py
from dataclasses import dataclass


@dataclass
class NewsItem:
    source: str
    title: str
    url: str
    published_at: str
    summary: str
    language: str
```

```python
# skills/sg-news-digest/scripts/pipeline/config.py
from dataclasses import dataclass
import os


@dataclass
class Settings:
    timezone: str = os.getenv("TIMEZONE", "Asia/Singapore")
    top_n: int = int(os.getenv("TOP_N", "5"))
```

```dotenv
# skills/sg-news-digest/config/defaults.env
TIMEZONE=Asia/Singapore
TOP_N=5
GOOGLE_NEWS_RSS=https://news.google.com/rss?hl=en-SG&gl=SG&ceid=SG:en
CNA_RSS=
ST_RSS=
ZAOBAO_RSS=
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_config_and_models.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/config/defaults.env skills/sg-news-digest/scripts/pipeline/models.py skills/sg-news-digest/scripts/pipeline/config.py skills/sg-news-digest/tests/test_config_and_models.py
git commit -m "feat: add settings and core news data model"
```

### Task 3: Implement RSS fetch client with retry/timeout

**Files:**
- Create: `skills/sg-news-digest/scripts/pipeline/rss_client.py`
- Test: `skills/sg-news-digest/tests/test_rss_client.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_rss_client.py
from skills.sg_news_digest.scripts.pipeline.rss_client import parse_feed


def test_parse_feed_extracts_entries():
    xml = """<rss><channel><item><title>A</title><link>https://a</link></item></channel></rss>"""
    entries = parse_feed(xml)
    assert len(entries) == 1
    assert entries[0]["title"] == "A"
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_rss_client.py -v`
Expected: FAIL due to missing module/function.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/rss_client.py
import feedparser
import requests


def fetch_feed(url: str, timeout: int = 15) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_feed(xml_text: str) -> list[dict]:
    parsed = feedparser.parse(xml_text)
    return [{"title": e.get("title", ""), "link": e.get("link", "")} for e in parsed.entries]
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_rss_client.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/pipeline/rss_client.py skills/sg-news-digest/tests/test_rss_client.py
git commit -m "feat: add RSS fetch and parse utilities"
```

### Task 4: Build source adapters for 4 news providers

**Files:**
- Create: `skills/sg-news-digest/scripts/sources/__init__.py`
- Create: `skills/sg-news-digest/scripts/sources/google_news.py`
- Create: `skills/sg-news-digest/scripts/sources/cna.py`
- Create: `skills/sg-news-digest/scripts/sources/straits_times.py`
- Create: `skills/sg-news-digest/scripts/sources/zaobao.py`
- Create: `skills/sg-news-digest/scripts/pipeline/source_fetcher.py`
- Test: `skills/sg-news-digest/tests/test_source_fetcher.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_source_fetcher.py
from skills.sg_news_digest.scripts.pipeline.source_fetcher import list_enabled_sources


def test_list_enabled_sources_returns_four_sources_by_default():
    names = list_enabled_sources()
    assert set(names) == {"google_news", "cna", "straits_times", "zaobao"}
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_source_fetcher.py -v`
Expected: FAIL due to missing `source_fetcher` implementation.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/source_fetcher.py
SOURCES = ["google_news", "cna", "straits_times", "zaobao"]


def list_enabled_sources() -> list[str]:
    return SOURCES.copy()
```

```python
# skills/sg-news-digest/scripts/sources/google_news.py
def fetch():
    return []
```

```python
# Repeat minimal fetch() stubs in cna.py, straits_times.py, zaobao.py
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_source_fetcher.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/sources skills/sg-news-digest/scripts/pipeline/source_fetcher.py skills/sg-news-digest/tests/test_source_fetcher.py
git commit -m "feat: add source adapter interfaces and source registry"
```

### Task 5: Normalize fields and filter Singapore-day window

**Files:**
- Create: `skills/sg-news-digest/scripts/pipeline/normalize.py`
- Test: `skills/sg-news-digest/tests/test_normalize.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_normalize.py
from skills.sg_news_digest.scripts.pipeline.normalize import is_same_sg_day


def test_is_same_sg_day_accepts_item_on_target_day():
    assert is_same_sg_day("2026-03-04T01:00:00Z", "2026-03-04")
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_normalize.py -v`
Expected: FAIL due to missing helper.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/normalize.py
from datetime import datetime
from zoneinfo import ZoneInfo


def is_same_sg_day(iso_time: str, target_date: str) -> bool:
    dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    sg = dt.astimezone(ZoneInfo("Asia/Singapore")).date().isoformat()
    return sg == target_date
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_normalize.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/pipeline/normalize.py skills/sg-news-digest/tests/test_normalize.py
git commit -m "feat: add normalization and Singapore-day filter"
```

### Task 6: Add pre-dedup URL/title filtering and geo/topic scope

**Files:**
- Create: `skills/sg-news-digest/scripts/pipeline/pre_dedup_filter.py`
- Test: `skills/sg-news-digest/tests/test_pre_dedup_filter.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_pre_dedup_filter.py
from skills.sg_news_digest.scripts.pipeline.pre_dedup_filter import dedup_urls


def test_dedup_urls_removes_duplicates():
    items = [{"url": "https://a"}, {"url": "https://a"}, {"url": "https://b"}]
    out = dedup_urls(items)
    assert len(out) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_pre_dedup_filter.py -v`
Expected: FAIL due to missing implementation.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/pre_dedup_filter.py
def dedup_urls(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for item in items:
        u = item.get("url", "")
        if u and u not in seen:
            seen.add(u)
            out.append(item)
    return out
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_pre_dedup_filter.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/pipeline/pre_dedup_filter.py skills/sg-news-digest/tests/test_pre_dedup_filter.py
git commit -m "feat: add pre-dedup URL filtering"
```

### Task 7: Implement Codex-powered semantic clustering with schema

**Files:**
- Create: `skills/sg-news-digest/schemas/event_clusters.schema.json`
- Create: `skills/sg-news-digest/scripts/pipeline/semantic_processor.py`
- Test: `skills/sg-news-digest/tests/test_semantic_processor.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_semantic_processor.py
from skills.sg_news_digest.scripts.pipeline.semantic_processor import build_prompt


def test_prompt_mentions_top5_and_chinese_output():
    text = build_prompt([{"title": "A", "source": "cna"}], top_n=5)
    assert "Top 5" in text
    assert "中文" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_semantic_processor.py -v`
Expected: FAIL due to missing module.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/semantic_processor.py
import json
import subprocess
from pathlib import Path


def build_prompt(items: list[dict], top_n: int) -> str:
    return (
        f"请对输入新闻做语义去重和分类，输出Top {top_n}，语言中文。"
        f"\n输入JSON:\n{json.dumps(items, ensure_ascii=False)}"
    )


def run_semantic(items: list[dict], top_n: int, schema_path: Path, out_path: Path) -> str:
    prompt = build_prompt(items, top_n)
    cmd = [
        "codex", "exec", "--skip-git-repo-check",
        "--output-schema", str(schema_path),
        "-o", str(out_path),
        prompt,
    ]
    subprocess.run(cmd, check=True)
    return out_path.read_text(encoding="utf-8")
```

```json
// skills/sg-news-digest/schemas/event_clusters.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["clusters"],
  "properties": {
    "clusters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["event_title", "category", "importance", "items"],
        "properties": {
          "event_title": {"type": "string"},
          "category": {"type": "string"},
          "importance": {"type": "number"},
          "items": {"type": "array"}
        }
      }
    }
  }
}
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_semantic_processor.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/schemas/event_clusters.schema.json skills/sg-news-digest/scripts/pipeline/semantic_processor.py skills/sg-news-digest/tests/test_semantic_processor.py
git commit -m "feat: add codex semantic clustering adapter"
```

### Task 8: Rank clusters and select Top 5

**Files:**
- Create: `skills/sg-news-digest/scripts/pipeline/ranking.py`
- Test: `skills/sg-news-digest/tests/test_ranking.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_ranking.py
from skills.sg_news_digest.scripts.pipeline.ranking import select_top_clusters


def test_select_top_clusters_limits_count():
    clusters = [{"importance": i} for i in range(10)]
    result = select_top_clusters(clusters, top_n=5)
    assert len(result) == 5
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_ranking.py -v`
Expected: FAIL due to missing function.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/ranking.py
def select_top_clusters(clusters: list[dict], top_n: int = 5) -> list[dict]:
    ordered = sorted(clusters, key=lambda x: x.get("importance", 0), reverse=True)
    return ordered[:top_n]
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_ranking.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/pipeline/ranking.py skills/sg-news-digest/tests/test_ranking.py
git commit -m "feat: add ranking and top5 selector"
```

### Task 9: Render Chinese Markdown report with insights/takeaways

**Files:**
- Create: `skills/sg-news-digest/scripts/pipeline/report_generator.py`
- Create: `skills/sg-news-digest/templates/report.md.tmpl`
- Test: `skills/sg-news-digest/tests/test_report_generator.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_report_generator.py
from skills.sg_news_digest.scripts.pipeline.report_generator import render_report


def test_render_report_contains_required_sections():
    md = render_report("2026-03-04", [])
    assert "## 今日执行摘要" in md
    assert "## 今日关键 Insights" in md
    assert "## 今日 Takeaways" in md
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_report_generator.py -v`
Expected: FAIL due to missing module.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/report_generator.py
def render_report(report_date: str, clusters: list[dict]) -> str:
    lines = [
        f"# 新加坡与国际重大新闻日报（{report_date}）",
        "",
        "## 今日执行摘要",
        "",
        "## Top 5 新闻详解",
        "",
        "## 今日关键 Insights",
        "",
        "## 今日 Takeaways",
        "",
        "## 数据覆盖与局限说明",
    ]
    return "\n".join(lines)
```

```text
# skills/sg-news-digest/templates/report.md.tmpl
# 新加坡与国际重大新闻日报（{{ report_date }})
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_report_generator.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/pipeline/report_generator.py skills/sg-news-digest/templates/report.md.tmpl skills/sg-news-digest/tests/test_report_generator.py
git commit -m "feat: add markdown report renderer with required sections"
```

### Task 10: Wire end-to-end runner and shell entrypoint

**Files:**
- Create: `skills/sg-news-digest/scripts/pipeline/runner.py`
- Modify: `skills/sg-news-digest/scripts/run.sh`
- Test: `skills/sg-news-digest/tests/test_runner.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_runner.py
from skills.sg_news_digest.scripts.pipeline.runner import parse_args


def test_parse_args_default_top5():
    args = parse_args([])
    assert args.top == 5
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_runner.py -v`
Expected: FAIL due to missing runner.

**Step 3: Write minimal implementation**

```python
# skills/sg-news-digest/scripts/pipeline/runner.py
import argparse


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=None)
    p.add_argument("--top", type=int, default=5)
    return p.parse_args(argv)
```

```bash
# skills/sg-news-digest/scripts/run.sh
#!/usr/bin/env bash
set -euo pipefail
python -m skills.sg_news_digest.scripts.pipeline.runner "$@"
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_runner.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/scripts/pipeline/runner.py skills/sg-news-digest/scripts/run.sh skills/sg-news-digest/tests/test_runner.py
git commit -m "feat: add CLI runner and shell entrypoint"
```

### Task 11: Add degradation/failure-path behavior tests

**Files:**
- Create: `skills/sg-news-digest/tests/test_degradation_paths.py`
- Modify: `skills/sg-news-digest/scripts/pipeline/runner.py`

**Step 1: Write the failing test**

```python
# skills/sg-news-digest/tests/test_degradation_paths.py
from skills.sg_news_digest.scripts.pipeline.runner import build_limitations_text


def test_limitations_mentions_source_failure():
    text = build_limitations_text(failed_sources=["cna"], degraded=True, count=3, target=5)
    assert "来源受限" in text
    assert "CNA" in text.upper()
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_degradation_paths.py -v`
Expected: FAIL due to missing helper.

**Step 3: Write minimal implementation**

```python
# add in runner.py

def build_limitations_text(failed_sources: list[str], degraded: bool, count: int, target: int) -> str:
    parts = []
    if failed_sources:
        parts.append(f"来源受限: {', '.join(failed_sources)}")
    if degraded:
        parts.append("AI语义处理降级为规则模式")
    if count < target:
        parts.append(f"当日有效新闻不足{target}条，实际输出{count}条")
    return "；".join(parts)
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_degradation_paths.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/tests/test_degradation_paths.py skills/sg-news-digest/scripts/pipeline/runner.py
git commit -m "test: cover degraded-mode and source-failure messaging"
```

### Task 12: Finalize skill contract docs and verification commands

**Files:**
- Modify: `skills/sg-news-digest/SKILL.md`
- Create: `skills/sg-news-digest/README.md`
- Modify: `skills/sg-news-digest/pyproject.toml`

**Step 1: Write the failing test**

```python
# append to skills/sg-news-digest/tests/test_smoke.py

def test_skill_doc_mentions_openclaw_boundary():
    text = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "不负责 cron" in text
    assert "stdout" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest skills/sg-news-digest/tests/test_smoke.py::test_skill_doc_mentions_openclaw_boundary -v`
Expected: FAIL until SKILL.md is populated.

**Step 3: Write minimal implementation**

```markdown
<!-- skills/sg-news-digest/SKILL.md -->
# sg-news-digest

- 输入：`--date`(可选), `--top`(默认5)
- 输出：stdout 为中文 Markdown, stderr 为结构化日志
- 边界：不负责 cron；不负责 Telegram 发送
- 依赖：Codex CLI, Python 3.11+, 网络访问
```

```markdown
<!-- skills/sg-news-digest/README.md -->
## Verify

```bash
pytest skills/sg-news-digest/tests -v
bash skills/sg-news-digest/scripts/run.sh --date 2026-03-04 --top 5
```
```

**Step 4: Run test to verify it passes**

Run: `pytest skills/sg-news-digest/tests/test_smoke.py::test_skill_doc_mentions_openclaw_boundary -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/sg-news-digest/SKILL.md skills/sg-news-digest/README.md skills/sg-news-digest/pyproject.toml skills/sg-news-digest/tests/test_smoke.py
git commit -m "docs: finalize skill contract and verification instructions"
```

## Final Verification Checklist (must run before completion)

1. `pytest skills/sg-news-digest/tests -v`
Expected: all tests pass.

2. `bash skills/sg-news-digest/scripts/run.sh --date 2026-03-04 --top 5 > /tmp/sg_digest.md`
Expected: exit code `0` or `2`, markdown generated.

3. `rg "## 今日关键 Insights|## 今日 Takeaways" /tmp/sg_digest.md`
Expected: both sections exist.

4. Manual read-through:
- Confirm output is Chinese.
- Confirm exactly up to 5 items in Top section.
- Confirm every item includes summary + impact + risk/opportunity + source links.

## Risks and Mitigations

- RSS endpoint instability: keep per-source timeout/retry and failure isolation.
- LLM output drift: enforce JSON schema with `--output-schema` and fallback path.
- Paywall content sparsity: confidence notes + limitation section.
- Source URL unknown at bootstrap: keep configurable env vars and validate at startup.

## Suggested First Execution Order

1. Task 1-3 (foundation)
2. Task 4-6 (ingest and filtering)
3. Task 7-9 (semantic + report core)
4. Task 10-12 (runner, degradations, docs)
5. Final verification checklist
