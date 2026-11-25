# Zz竞彩分析

竞彩足球赛事台账建模与复盘工具。基于竞彩官方固定奖金赔率，反算去水隐含概率、理论返还率、概率-支持率偏差并做信号分级，输出台账表格与快照长图；支持历史台账回填后的命中率、ROI、最大回撤回测。

> ⚠ 仅数据统计展示，不构成购彩建议，不预测赛果；合法购彩仅限线下实体门店。

## 目录结构

```
zz-jingcai-analysis/
├── SKILL.md                          # 技能说明、工作流、脚本用法、合规要求
├── scripts/
│   ├── build_ledger.py               # 台账快照：JSON → HTML / CSV / PNG
│   └── backtest_ledger.py            # 历史回测：台账 CSV → 回测报告 + 逐笔明细
└── references/
    ├── data_schema.md                # 字段定义、去水概率/RTP/偏差/信号分级公式、回测指标
    └── compliance.md                  # 合规红线、允许/禁止事项、数据来源口径
```

## 快速开始

依赖：Python 3.9+。

```bash
# 生成当日台账快照（输入为符合 schema 的赛事 JSON）
python3 scripts/build_ledger.py --input matches.json --out ./output

# 赛后回测（输入为回填赛果的历史台账 CSV）
python3 scripts/backtest_ledger.py --input backtest.csv --out ./output
```

### PNG 长图渲染

脚本会自动探测本机浏览器（`CHROME_PATH` 环境变量 → Linux chromium/chrome → Windows Chrome/Edge 默认路径），两套渲染路径任选其一：

1. 已安装 `playwright`：全页截图，效果最好
2. 未安装 `playwright`：自动降级为 Chrome/Edge 无头 `--screenshot`，再用 Pillow 裁掉底部空白（无 Pillow 也能出图，仅留白边）

两者都不可用时脚本会报错并保留 HTML/CSV，不会输出半成品图。

## 字段与口径

- 字段定义、计算公式、信号分级与回测指标：见 [references/data_schema.md](references/data_schema.md)
- 合规红线、允许/禁止事项：见 [references/compliance.md](references/compliance.md)（强制执行）

## 数据来源

- 竞彩官方：`https://www.lottery.gov.cn/`、`https://www.sporttery.cn/`
- 官方仅开售竞彩固定奖金玩法；亚盘、欧赔、外围水位不属于官方口径，不得作为台账定价依据。
- 赔率为抓取时点固定值，浮动以出票时刻为准。

## 合规声明

本项目仅用于赛事数据归档、赔率概率统计、台账复盘与历史回测。不预测赛果、不推单、不引导购彩、不承诺盈利、不编造数据；不涉及外围盘口与地下赌球。
