# -*- coding: utf-8 -*-
"""
竞彩台账历史回测脚本
读取已回填赛果的台账 CSV，计算命中率、ROI、最大回撤等历史复盘指标。

输入 CSV 字段（列名可按顺序，缺失则留空）：
  code, league, home, away, market, final_result, bet_select, odds, stake
  - final_result : 最终赛果，取值 主胜 / 平 / 客胜
  - bet_select   : 投注选项，取值 主胜 / 平 / 客胜
  - odds         : 命中时的固定奖金赔率
  - stake        : 单笔本金（元）

输出：
  - 回测汇总 Markdown 报告
  - 逐笔明细 CSV（含 hit、回款、累计净值、回撤）

合规：仅历史数据复盘，不预测未来赛果、不构成购彩建议。

用法：
  python3 backtest_ledger.py --input backtest.csv --out ./output
"""
import argparse, csv, pathlib, html

RESULT_MAP = {"主胜": "主胜", "平": "平", "客胜": "客胜"}

def load_rows(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if not r.get("final_result") and not r.get("bet_select"):
                continue
            try:
                odds = float(r.get("odds") or 0)
                stake = float(r.get("stake") or 0)
            except ValueError:
                continue
            rows.append(dict(
                code=r.get("code", ""), league=r.get("league", ""),
                home=r.get("home", ""), away=r.get("away", ""),
                market=r.get("market", ""),
                final=r.get("final_result", "").strip(),
                select=r.get("bet_select", "").strip(),
                odds=odds, stake=stake,
            ))
    return rows

def run(rows):
    total = len(rows)
    hit = 0
    total_stake = 0.0
    total_return = 0.0
    peak = 0.0
    max_dd = 0.0
    cum_net = 0.0
    detail = []

    for r in rows:
        is_hit = r["select"] == r["final"] and r["final"] in RESULT_MAP
        ret = r["stake"] * r["odds"] if is_hit else 0.0
        net = ret - r["stake"]
        cum_net += net
        peak = max(peak, cum_net)
        dd = cum_net - peak  # 负值
        max_dd = min(max_dd, dd)
        if is_hit:
            hit += 1
        total_stake += r["stake"]
        total_return += ret
        detail.append({**r, "hit": int(is_hit), "return": ret,
                        "cum_net": cum_net, "drawdown": dd})

    profit = total_return - total_stake
    roi = (profit / total_stake * 100) if total_stake > 0 else 0.0
    hit_rate = (hit / total * 100) if total > 0 else 0.0

    summary = dict(
        total=total, hit=hit, hit_rate=hit_rate,
        total_stake=total_stake, total_return=total_return,
        profit=profit, roi=roi, max_drawdown=max_dd,
    )
    return summary, detail

def write_detail(detail, path):
    cols = ["code", "league", "home", "away", "market", "final", "select",
            "odds", "stake", "hit", "return", "cum_net", "drawdown"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in detail:
            w.writerow({k: d.get(k, "") for k in cols})

def write_report(summary, path):
    s = summary
    lines = [
        "# 竞彩台账历史回测报告",
        "",
        "| 指标 | 数值 |",
        "|---|---|",
        f"| 总场次 | {s['total']} |",
        f"| 命中数 | {s['hit']} |",
        f"| 命中率 | {s['hit_rate']:.1f}% |",
        f"| 总本金 | {s['total_stake']:.2f} 元 |",
        f"| 总回款 | {s['total_return']:.2f} 元 |",
        f"| 净利润 | {s['profit']:.2f} 元 |",
        f"| ROI | {s['roi']:.2f}% |",
        f"| 最大回撤（累计净值） | {s['max_drawdown']:.2f} 元 |",
        "",
        "> 仅历史数据统计复盘，不预测未来赛果，不构成购彩建议；合法购彩仅限线下实体门店。",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="回填赛果的历史台账 CSV")
    ap.add_argument("--out", required=True, help="输出目录")
    args = ap.parse_args()

    rows = load_rows(args.input)
    summary, detail = run(rows)

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = out / "回测报告.md"
    detail_csv = out / "回测明细.csv"
    write_report(summary, report)
    write_detail(detail, detail_csv)

    print(f"总场次 {summary['total']} | 命中 {summary['hit']} | 命中率 {summary['hit_rate']:.1f}%")
    print(f"ROI {summary['roi']:.2f}% | 净利润 {summary['profit']:.2f} | 最大回撤 {summary['max_drawdown']:.2f}")
    print(f"报告: {report}\n明细: {detail_csv}")

if __name__ == "__main__":
    main()
