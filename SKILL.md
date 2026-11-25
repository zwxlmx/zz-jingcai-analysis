---
name: jingcai-analysis-ledger
description: Zz竞彩分析 —— 竞彩足球赛事分析台账建模与复盘工具。录入联赛、排名、积分、近期状态、攻防、交锋、伤病、教练风格、主客场及官方竞彩赔率/支持率等因子，自动计算赔率去水隐含概率、理论返还率、概率-支持率偏差与信号分级，输出因子矩阵 JSON、Markdown/CSV 台账表和 HTML/PNG 快照长图；支持历史台账回填后的命中率、ROI、最大回撤回测。当用户需要整理竞彩/足球赛事数据、生成赛事分析台账快照、做多场批量数据入库、或对历史投注记录做复盘统计时使用。仅做数据归档与统计复盘，不预测赛果、不推单、不引导购彩。
---

# Zz竞彩分析 · 竞彩赛事分析台账建模

## 概述

把一场或多场竞彩赛事的公开因子整理成结构化台账：基于官方固定奖金赔率反算去水概率与返还率，对照官方支持率生成定价-热度偏差和信号分级，交付可留存比对的表格与快照长图。所有指标只描述赔率定价与群众热度，**不输出胜负倾向**。

## 工作流

1. **采集官方数据**：用浏览器访问竞彩官网（`lottery.gov.cn` / `sporttery.cn`）足球胜平负/让球胜平负页面，抓取当日场次、编号、联赛、开赛时间、主客队、固定奖金赔率、公开支持率与开售状态；伤停、交锋、近期状态等因子来自公开可核验来源，缺失留空，不臆造。字段口径见 [references/data_schema.md](references/data_schema.md)。
2. **组装输入 JSON**：按 schema 填 `match_list`，每场一个 `market` 数组（胜平负、让球胜平负可各一条）。
3. **运行生成脚本**：调用 `scripts/build_ledger.py`，输出 HTML、CSV、PNG 到指定目录。
4. **交付与复核**：交付 PNG 快照与 CSV 数据表；核对概率、返还率、信号分级与脚本输出一致；快照末尾保留合规声明。
5. **赛后回填（回测）**：历史场次补填 `final_result / stake / bet_select`，按 data_schema 第 4 节公式计算命中率、ROI、最大回撤，仅作历史复盘。

## 脚本用法

### 台账快照生成

```bash
python3 scripts/build_ledger.py --input matches.json --out ./output
```

- `--input`：符合 schema 的赛事 JSON
- `--out`：输出目录（自动创建）
- 产物：`台账_<batch>.html`、`台账_<batch>.csv`、`台账_<batch>.png`

### 历史回测

```bash
python3 scripts/backtest_ledger.py --input backtest.csv --out ./output
```

- `--input`：回填赛果的历史台账 CSV（字段见 data_schema 第 4 节）
- 产物：`回测报告.md`（命中率/ROI/最大回撤汇总）、`回测明细.csv`（逐笔回款、累计净值、回撤）

### 渲染依赖（PNG 长图）

脚本按优先级自动探测本机浏览器：环境变量 `CHROME_PATH` → Linux 下 chromium/chrome → Windows 下 Chrome/Edge 默认安装路径。

- 装了 `playwright`：走 playwright 全页截图（`full_page=True`）
- 没装 playwright：自动降级为 Chrome/Edge 无头 `--screenshot`，再用 Pillow 裁掉底部空白；无 Pillow 时保留原截图，不报错
- 两者都没有：抛出提示，先交付 HTML 与 CSV，PNG 标注为待补

## 输入模式

| 模式 | 做法 |
|---|---|
| 单场分析 | `match_list` 只放一场，输出单场因子矩阵 + 单行台账 |
| 批量入库 | 多场多条 `market`，合并为统一台账表 |
| 回测统计 | 跑 `scripts/backtest_ledger.py`，读已回填赛果的历史台账，计算命中率/ROI/最大回撤（公式见 data_schema） |
| 导出台账 | 只输出纯净 CSV/Markdown 表，不附加分析文字 |

## 参考文件

- [references/data_schema.md](references/data_schema.md)：JSON 字段定义、概率/返还率/偏差/信号分级公式、回测指标算法
- [references/compliance.md](references/compliance.md)：合规红线、允许/禁止事项、数据来源口径（强制执行）

## 合规要求（强制）

- 不预测赛果、不推单、不引导购彩、不承诺盈利、不编造数据；不涉及外围盘口与地下赌球。
- 每份台账/快照末尾固定声明：**仅数据统计展示，不构成购彩建议，不预测赛果；合法购彩仅限线下实体门店。**
- 详见 [references/compliance.md](references/compliance.md)，与本文件冲突时以合规要求为准。
