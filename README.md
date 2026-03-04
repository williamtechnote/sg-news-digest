# SG News Digest

一个可被 OpenClaw 定时调用的 Codex Skill：从 Google News、The Straits Times、CNA、联合早报获取当天新闻，进行语义去重、归类和分析，输出中文高价值日报（Markdown）。

## 目标

- 抓取当天新闻（新加坡 + 国际重大新闻）
- 用 Codex CLI 做语义去重与事件聚类
- 输出 `Top 5` 重点新闻分析
- 产出包含 `Insights` 和 `Takeaways` 的中文报告

## 边界

- 本项目负责：抓取、清洗、去重、分析、Markdown 生成
- OpenClaw 负责：`cron` 调度和 Telegram 发送

## 数据源

默认使用官方/公开 RSS 或公开可访问源：

- Google News RSS
- CNA RSS
- The Straits Times RSS
- 联合早报（默认使用 Google News `site:zaobao.com.sg` 回退源）

配置文件：`skills/sg-news-digest/config/defaults.env`

## 输出格式

运行成功后：

- `stdout`：中文 Markdown 日报（可直接发 Telegram）
- `stderr`：结构化 JSON 日志（便于 OpenClaw 记录）

报告包含：

- 今日执行摘要
- Top 5 新闻详解（摘要/影响分析/风险机会/来源）
- 今日关键 Insights
- 今日 Takeaways
- 数据覆盖与局限说明

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
.venv/bin/pip install pytest requests feedparser python-dateutil pyyaml
```

### 2. 运行测试

```bash
.venv/bin/pytest skills/sg-news-digest/tests -q
```

### 3. 生成日报

```bash
bash skills/sg-news-digest/scripts/run.sh --date 2026-03-04 --top 5
```

常用参数：

- `--date YYYY-MM-DD`：指定新加坡自然日（默认当天）
- `--top N`：输出数量（默认 `5`）
- `--no-ai`：禁用 Codex 语义分析，使用规则降级流程
- `--env-file <path>`：使用自定义配置文件

## OpenClaw 集成示例

> 下面只展示集成思路，具体命令以你的 OpenClaw 环境为准。

1. 在 OpenClaw 中配置 cron 定时执行：

```bash
bash /path/to/sg-news-digest/skills/sg-news-digest/scripts/run.sh --top 5
```

2. 将命令 `stdout` 作为消息正文转发到 Telegram。

## 配置项（关键）

位于 `skills/sg-news-digest/config/defaults.env`：

- `TIMEZONE`（默认 `Asia/Singapore`）
- `TOP_N`（默认 `5`）
- `REQUEST_TIMEOUT` / `REQUEST_RETRIES`
- `SEMANTIC_TIMEOUT`
- `CODEX_MODEL`（可选）
- `GOOGLE_NEWS_RSS` / `CNA_RSS` / `ST_RSS` / `ZAOBAO_RSS`

## 退出码

- `0`：成功（AI 语义链路正常）
- `2`：部分成功（例如来源受限或降级）
- `1`：失败（无法生成报告）

## 目录结构

```text
skills/sg-news-digest/
  SKILL.md
  config/defaults.env
  schemas/event_clusters.schema.json
  scripts/run.sh
  scripts/pipeline/*.py
  scripts/sources/*.py
  tests/*.py
docs/plans/
```

## 许可证

见根目录 `LICENSE`。
