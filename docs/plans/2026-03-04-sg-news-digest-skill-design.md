# SG News Digest Codex Skill 设计文档

- 日期：2026-03-04
- 目标：构建一个可被 OpenClaw 调用的 Codex Skill，从 Google News、The Straits Times、CNA、联合早报获取当日新闻，进行语义去重、归类与分析，输出中文高价值日报（Markdown），供 OpenClaw 转发至 Telegram。

## 1. 范围与边界

### 1.1 In Scope
- 抓取官方/公开 RSS 或 API（不做网页抓取）
- 多源新闻标准化
- 规则预去重 + LLM 语义聚类去重
- 固定大类 + 动态子类分类
- 影响/风险/机会导向分析
- 输出中文 Markdown 报告（stdout）

### 1.2 Out of Scope
- 不负责调度（cron 由 OpenClaw 配置）
- 不负责 Telegram 发送（由 OpenClaw 执行）
- 不依赖付费内容访问（付费墙内容降级处理）

## 2. 关键需求（已确认）

- 数据源策略：仅官方/公开 RSS/API
- 输出格式：纯 Markdown
- 最终输出条数：Top 5（避免信息爆炸）
- 覆盖范围：新加坡 + 国际重大新闻
- 付费墙策略：使用公开可访问字段降级分析
- 语义去重强度：平衡（同一事件多源通常合并）
- 分类策略：固定大类 + 动态子类
- 分析风格：决策支持型（影响、风险、机会）
- 条目字段：标题 + 摘要 + 影响分析 + 风险/机会 + 来源链接
- 数量不足策略：不足 5 条时按实际输出并声明来源受限

## 3. 方案选择

### 3.1 备选方案
1. 规则化采集 + 单次 LLM 语义处理流水线（推荐）
2. 事件图谱两阶段 LLM 流水线
3. 规则优先、LLM 仅总结

### 3.2 选择结论
采用方案 1：在稳定性、交付速度、维护成本之间最平衡，并保留后续升级到两阶段事件图谱的扩展点。

## 4. 总体架构

1. Ingest：从四个来源拉取当天候选新闻
2. Normalize：字段归一（标题、摘要、发布时间、来源、URL、语言、抓取时间）
3. Filter：范围初筛 + URL/标题规则去重
4. Semantic Merge：LLM 语义聚类、事件级合并、分类、评分
5. Rank & Select：按影响力/时效/多源验证选 Top 5
6. Analyze：生成摘要、影响分析、风险/机会
7. Render：生成中文 Markdown 报告
8. Exit：stdout 输出报告，stderr 输出结构化日志与状态

## 5. 组件设计与数据流

### 5.1 组件
- `source_fetcher`：来源抓取与重试/超时
- `normalizer`：标准字段模型与时区统一（Asia/Singapore）
- `pre_dedup_filter`：规则预去重与当日时间窗过滤
- `semantic_processor`：LLM 聚类、分类、评分
- `report_generator`：Top 5 报告生成
- `runner`：流程编排与退出码管理

### 5.2 数据对象（逻辑）
- `NewsItem`：标准新闻条目
- `EventCluster`：事件聚类结果（代表新闻、来源集合、评分、分类）
- `DigestReport`：最终报告结构

## 6. 错误处理与降级

1. 来源失败隔离：单源失败不阻断整体
2. 付费墙降级：公开字段参与分析并标注置信度下降
3. LLM 失败降级：回退规则去重 + 模板化简报
4. 条目不足：按实际输出并在摘要声明
5. 可观测性：结构化日志记录每阶段计数、耗时、失败源

### 6.1 退出码约定
- `0`：成功（允许部分来源失败但有完整报告）
- `1`：失败（无法输出报告）
- `2`：部分成功（报告可用但触发关键降级）

## 7. 报告结构（Markdown）

1. 今日执行摘要
2. Top 5 新闻详解（每条包含）：
   - 标题
   - 摘要
   - 影响分析
   - 风险/机会
   - 来源链接（至少 1 条，优先多源）
3. 今日关键 Insights（跨条目洞察）
4. 今日 Takeaways（可执行建议）
5. 数据覆盖与局限说明

## 8. 测试与验收标准

### 8.1 测试
- 单元测试：归一化、去重、排序、渲染
- 集成测试：固定 feed fixture 的全链路输出
- 降级测试：来源失败、LLM 失败、条目不足

### 8.2 验收标准（DoD）
- 输入：默认当天，可选 `--date YYYY-MM-DD`
- 输出：可直接用于 Telegram 发送的中文 Markdown
- 规模：最多 Top 5
- 稳定性：部分来源失败仍可产出
- 可运维：日志可定位故障阶段

## 9. 建议目录结构

```text
skills/sg-news-digest/
  SKILL.md
  scripts/
    run.sh
    sources/
    pipeline/
  templates/
    report.md.tmpl
  tests/
  config/
    defaults.env
```

## 10. OpenClaw 集成契约

- Skill 输入：可选日期参数，默认新加坡当天
- Skill 输出：stdout 为 Markdown，stderr 为日志
- OpenClaw 责任：cron 触发 + Telegram 转发

## 11. 后续计划

下一步按 writing-plans 技能输出详细实现计划（任务拆分、依赖、测试顺序、里程碑与风险）。
