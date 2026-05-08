# Region Map — 公司攻坚依赖图

跨产品、跨 org 的 epic 级攻坚地图。一张图看懂全公司在攻什么、被什么卡住、哪些已经成熟。

源自 newmath BEDC viz, 复用 closure-tier 心智模型 (单调闭合, 不回退, mature 后封档)。

## 单一事实源 / Single source of truth

**GitHub (源码 + issues + PRs + project boards) 是唯一事实源。** 每个 region 必须能映射到 GitHub 上的某个具体存在 (issue / PR / 代码目录 / release / project board column)。

不能做 region 的:
- 内部 doc / GTM artifact (e.g. `internal/*.md`, Excel CRM, 教程草稿)
- 纯概念聚合 (没有任何 issue / PR / 代码 backing 的"理念节点")
- 跨产品的"未来集成"占位 (等真有 issue 再开)

closure 阶段的 trigger 必须有 GitHub 证据:
- `seed`: issue / discussion 已建
- `obligation`: issue 有 assignee
- `scoped`: RFC / ADR / design doc PR 已 merge
- `public`: release / changelog / blog 公开
- `bridged`: 上下游 issue closed + smoke 通过
- `mature`: **30 天 incident-free** (有 release tag + 30 天内无新 bug)

`mature` 是高门槛 — 仅靠"功能能用"不够, 需要 30 天稳定运行。带近期 bug / 频繁迭代 / 无 release tag 的功能是 `public`, 不是 `mature`。

每个 region 应该有 `gh_query` 字段, 让 weekly audit (`audit.yml`) 自动对账实际 issue 数 vs 声称的 `issue_count`, 漂移自动报告。

## 在线访问 / Live

发布在 GitHub Pages: <https://chronoaiproject.github.io/region-map/visualization.html>

每次 push 到 `main` 自动 build + 发布 (见 `.github/workflows/publish.yml`)。

## 快速开始 / Quick Start

```bash
quarto preview
```

打开浏览器到 `http://localhost:<port>`, 默认中文界面, 顶部 EN/ZH 切换。

设计原理 / 数据模型详见 [`ARCHITECTURE.md`](ARCHITECTURE.md)。

## 三层结构 / Three-Layer Structure

| 层 | 文件 | 谁改 / 何时改 |
| --- | --- | --- |
| 代码 | `visualization.qmd`, `_quarto.yml`, `assets/region-map.css` | viz 行为变化, 罕见 |
| 配置 | `config.json` | 加产品 / 调状态名 / 改颜色 / 切语言, 中频 |
| 业务数据 | `regions.json` | 状态推进 / 加 region, 高频 (周级) |

## 数据维护规则 / Data Maintenance Rules

### 状态机 (单调, 不回退)

```
seed → obligation → scoped → public → bridged → mature → (archived after 30d)
```

每次推进必须有客观 trigger event:

| Stage | trigger |
| --- | --- |
| `seed` (提出) | issue / discussion 创建 |
| `obligation` (接手) | assignee 字段非空 |
| `scoped` (设计完) | RFC / ADR / 设计 doc merged |
| `public` (已承诺) | release notes / changelog / 销售材料 / blog 已发 |
| `bridged` (已集成) | 上下游 issue closed + smoke 通过 |
| `mature` (运行中) | 30 天无 incident 稳定运行 |

### Promote 决策权

| Promote | 谁决定 |
| --- | --- |
| seed → obligation | owner 自己 |
| obligation → scoped | owner 自己 |
| scoped → public | 战略层批准 (因为承诺有外部性) |
| public → bridged | owner 自己 |
| bridged → mature | owner 自己 |
| mature → archived | 30 天无 attention 自动 |

### 不允许的操作

- 状态回退 (mature → bridged): incident 用新 region 解决, 不退化原节点
- v2 替代 v1: 两个 mature 节点并存, v1 不变 (历史保留)

## 文件 schema 速查 / Schema Quick Reference

### `config.json`
- `products[]` — 产品 enum: `{key, label.{en,zh}}`
- `closure_tiers[]` — 6 阶段定义: `{key, label.{en,zh}, color, trigger.{en,zh}}`
- `formal_levels[]` — 自动化等级: `{key, shape, label.{en,zh}}`
- `focus_quarter` — 红框规则: `{label.{en,zh}, border_color, border_width}`
- `archive_rule` — 封档规则: `{after_mature_days, opacity}`
- `ui` — i18n: `{title.{en,zh}, default_lang, legend.*}`

### `regions.json`
- `regions[<key>]` — region 实例:
  - `label.{en,zh}` — 节点显示标签
  - `desc.{en,zh}` — 详情面板描述
  - `closure` — 必须在 config.closure_tiers
  - `formal` — 必须在 config.formal_levels
  - `product` — 必须在 config.products
  - `milestone` — 自由文本 (e.g. M0 / Stage-A)
  - `owner` — GitHub username (对应 team.yaml)
  - `issue_count` — 节点大小驱动
  - `focus` — 红框
  - `archived` — 半透明
  - `promoted_at.{closure_key}` — 各阶段推进日期 (审计)
  - `deps[]` — 上游依赖 region key 列表

## 加新 region / Adding a New Region

1. 决定 region key (`<Product>-<EpicShortName>`, e.g. `NyxID-Foo-Bar`)
2. 在 `regions.json` 的 `regions` 对象里加一项, 按 schema 填字段
3. 如果它依赖已有 region, 在 `deps` 里写上游 key
4. 跑校验:
   ```bash
   cd tools && python3 validate_regions.py
   ```
5. 跑预览看效果
6. commit

## 加新产品 / Adding a New Product

1. 在 `config.json` 的 `products` 数组里加一项: `{"key": "<id>", "label": {"en": "...", "zh": "..."}}`
2. 在 `regions.json` 加几个该产品的 region (用上面的步骤)
3. 跑校验

不需要改任何代码。

## 校验 / Validators

```bash
cd tools
python3 validate_config.py
python3 validate_regions.py
python3 -m unittest test_validate.py
```

CI 在 PR 上自动跑这些 (见 `.github/workflows/validate.yml`), 失败阻 merge。

## 漂移检测 / Drift detection

可选给 region 加 `gh_query` 字段, audit 会拉 GitHub 实际 issue 数对比 `issue_count`:

```bash
python3 tools/audit_regions.py            # report only
python3 tools/audit_regions.py --strict   # exit 1 on drift
python3 tools/audit_regions.py --markdown # markdown report
```

CI workflow `.github/workflows/audit.yml`:
- PR 改动 `regions.json` → `--strict` 严格检测, 漂移阻 merge
- 每周一 SGT 09:00 (cron) → markdown report 评论到 "Weekly region drift audit" issue
- `workflow_dispatch` → 手动触发同上

`closure / formal / promoted_at / focus` 等 judgment 字段不自动推断, 保持人工维护。

## 构建 / Build

```bash
quarto render        # build 到 _site/
quarto preview       # 本地服务器, 改文件自动重载
```

注意: `quarto preview` 只 watch `.qmd` 源码; 改 `config.json` 或 `regions.json` 需要重启 preview 或跑 `quarto render` 才能看到效果。
