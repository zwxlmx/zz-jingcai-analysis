# 数据字段与计算口径

## 1. 输入 JSON 结构

```json
{
  "meta": {
    "batch": "周三261125",
    "date": "2026-11-25",
    "source": "中国竞彩官网",
    "odds_update_time": "2026-11-25 16:36",
    "generated_at": "2026-11-25 20:47"
  },
  "match_list": [
    {
      "code": "004",
      "league": "欧冠",
      "kickoff": "2026-11-26 01:45",
      "home_team": "斯拉维亚",
      "away_team": "比利亚雷",
      "market": [
        {
          "type": "胜平负",
          "handicap": "0（不让球）",
          "odds": [3.30, 3.65, 1.78],
          "support_pct": [16, 19, 65],
          "status": "未开赛"
        },
        {
          "type": "让球胜平负",
          "handicap": "+1（受让1）",
          "odds": [1.75, 3.80, 3.28],
          "support_pct": [33, 36, 31],
          "status": "未开赛"
        }
      ]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| code | string | 竞彩场次编号（去重计数用） |
| league | string | 联赛/赛事 |
| kickoff | string | 开赛时间 |
| home_team / away_team | string | 主/客队 |
| market[] | array | 该场在售玩法，可多个（胜平负、让球胜平负） |
| market.type | string | 玩法名 |
| market.handicap | string | 让球描述；`+` 为客让主（主队受让），`-` 为主让客 |
| market.odds | number[3] | [胜, 平, 负] 固定奖金；未开售填 `null` |
| market.support_pct | number[3] | [胜, 平, 负] 官方公开支持率（人数占比，%） |
| market.status | string | 未开赛 / 已开赛 / 已完赛 |

## 2. 计算公式

### 去水隐含概率
对赔率 $o_i$（$i \in \{胜,平,负\}$）：

$$
p_i = \frac{1/o_i}{\sum_{j} 1/o_j} \times 100\%
$$

### 理论返还率（RTP）

$$
\text{RTP} = \frac{1}{\sum_{j} 1/o_j} \times 100\%
$$

### 概率 − 支持率偏差
取该盘概率最高的选项 $b = \arg\max_i p_i$：

$$
\text{diff} = p_b - s_b \quad (\text{单位：pp})
$$

- diff 为正：赔率概率高于群众热度（定价相对看好、市场投注偏冷）
- diff 为负：群众热度高于赔率概率（大众更看好、定价偏冷）

## 3. 信号分级

| 信号 | 条件 | 含义 |
|---|---|---|
| 绿·共识 | 最高项概率 ≥ 60% 且 diff ≥ −5pp | 赔率与热度基本一致，强势项共识度高 |
| 橙·分歧 | 最高项概率 ≥ 60% 且 diff < −5pp | 强势项但群众热度明显高于定价 |
| 灰·中性 | 最高项概率 50%–60% | 有倾向但不强势 |
| 灰·弱势 | 最高项概率 < 50% | 无明显强势项 |

信号只描述赔率定价与投注热度的背离程度，**不代表赛果倾向**。

## 4. 回测指标（赛后复盘用）

### 输入 CSV 字段

| 字段 | 取值 | 说明 |
|---|---|---|
| code / league / home / away / market | 文本 | 场次与玩法标识，沿用台账 |
| final_result | 主胜 / 平 / 客胜 | 最终赛果（赛后回填） |
| bet_select | 主胜 / 平 / 客胜 | 投注选项 |
| odds | 数字 | 命中时的固定奖金赔率 |
| stake | 数字 | 单笔本金（元） |

命中判定：`bet_select == final_result`。

### 计算指标

台账回填 `final_result`、`stake`、`bet_select`、`odds` 后计算：

| 指标 | 公式 |
|---|---|
| 总场次 | $N$ |
| 命中数 | $H$（命中=投注选项与最终赛果一致） |
| 命中率 | $H / N$ |
| 总本金 | $\sum \text{stake}$ |
| 总回款 | 命中单：$\text{stake} \times \text{赔率}$；未命中：0 |
| 净利润 | 总回款 − 总本金 |
| ROI | $(\text{总回款} - \text{总本金}) / \text{总本金} \times 100\%$ |
| 累计净值 | 逐笔累加（回款 − 本金） |
| 最大回撤 | 累计净值曲线从峰值到后续最低点的最大跌幅（负值） |

回测只统计历史命中与资金表现，不据此预测未来场次。
