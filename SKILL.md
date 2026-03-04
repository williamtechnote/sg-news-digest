---
name: sg-news-digest
description: 生成新加坡与国际重大新闻中文日报。使用官方/公开 RSS 或 API 从 Google News、The Straits Times、CNA、联合早报抓取当日新闻，执行语义去重、分类和决策支持分析，输出含 Insights 与 Takeaways 的 Markdown 报告。用于被 OpenClaw 的 cron 任务调用并将结果转发到 Telegram。
---

# sg-news-digest

构建中文新闻分析日报（新加坡 + 国际重大新闻）的 Codex Skill。

## 目标
- 从官方/公开 RSS 或 API 抓取 Google News、The Straits Times、CNA、联合早报当日新闻。
- 使用 Codex CLI 进行语义去重、分类和决策支持分析。
- 输出可直接发送到 Telegram 的 Markdown。

## 输入
- `--date YYYY-MM-DD` (可选，默认 Asia/Singapore 当天)
- `--top N` (可选，默认 5)
- `--env-file PATH` (可选，自定义配置)
- `--no-ai` (可选，禁用 AI，使用规则降级流程)

## 输出
- `stdout`: 中文 Markdown 报告
- `stderr`: 结构化运行日志（JSON）
- 退出码:
  - `0`: 正常输出
  - `2`: 部分成功（如 AI 降级或有效事件不足）
  - `1`: 致命失败

## 集成边界
- 不负责 cron 调度（由 OpenClaw 配置）
- 不负责 Telegram 发送（由 OpenClaw 读取 stdout 后转发）

## 依赖
- Python 3.9+
- Codex CLI（`codex exec` 可用）
- 网络访问（用于 RSS/API 抓取）

## 说明
- 若联合早报直连 RSS 不稳定，默认配置会使用 `Google News site:zaobao.com.sg` 公开 RSS 作为回退来源。
