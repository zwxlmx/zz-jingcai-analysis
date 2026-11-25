# -*- coding: utf-8 -*-
"""
竞彩赛事分析台账生成器
输入：结构化 JSON（赛事 + 各玩法赔率/支持率）
输出：HTML 台账快照、CSV 数据表、PNG 长图（无头浏览器渲染）

合规：仅做赔率去水概率、返还率、概率-支持率偏差与信号分级统计；
不输出赛果预测、不做推单、不引导购彩。

用法：
  python3 build_ledger.py --input matches.json --out ./output
"""
import argparse, json, pathlib, asyncio, html, os, subprocess

# ---------- 计算 ----------

def implied_probs(odds):
    """赔率去水归一化，返回 (概率列表%, 返还率%)；odds 为 None 时返回 (None, None)"""
    if not odds or any(o is None for o in odds):
        return None, None
    inv = [1.0 / o for o in odds]
    tot = sum(inv)
    probs = [x / tot * 100 for x in inv]
    rtp = 100.0 / tot
    return probs, rtp

def signal(prob_best, diff):
    if prob_best >= 60:
        return "绿·共识" if diff >= -5 else "橙·分歧"
    if prob_best >= 50:
        return "灰·中性"
    return "灰·弱势"

def build_rows(match_list):
    rows = []
    for m in match_list:
        for mk in m.get("market", []):
            odds = mk.get("odds")
            support = mk.get("support_pct")
            probs, rtp = implied_probs(odds)
            row = dict(
                code=m.get("code", ""), league=m.get("league", ""),
                kickoff=m.get("kickoff", ""), home=m.get("home_team", ""),
                away=m.get("away_team", ""), mtype=mk.get("type", ""),
                handicap=mk.get("handicap", "0"), status=mk.get("status", ""),
                probs=probs, rtp=rtp, support=support,
                best=None, bestp=None, diff=None, sig=None,
            )
            if probs:
                bi = max(range(3), key=lambda i: (probs[i], support[i] if support else 0))
                row["best"] = ["主胜", "平", "客胜"][bi]
                row["bestp"] = probs[bi]
                row["diff"] = probs[bi] - support[bi] if support else None
                row["sig"] = signal(probs[bi], row["diff"] if row["diff"] is not None else 0)
            rows.append(row)
    return rows

# ---------- 渲染 ----------

def esc(s):
    return html.escape(str(s))

def render_html(meta, rows):
    sold = [r for r in rows if r["probs"]]
    finished = [r for r in rows if not r["probs"]]
    green = [r for r in sold if r["sig"].startswith("绿")]
    orange = [r for r in sold if r["sig"].startswith("橙")]
    high = [r for r in sold if r["bestp"] >= 60]
    avg_rtp = sum(r["rtp"] for r in sold) / len(sold) if sold else 0
    matches = len({r["code"] for r in sold})

    def cls(sig):
        if sig.startswith("绿"): return "sig-green"
        if sig.startswith("橙"): return "sig-orange"
        return "sig-gray"

    trs = []
    for r in rows:
        if not r["probs"]:
            prob = '<span class="muted">未开售／无赔率</span>'
            best = diff = rtp = '<span class="muted">—</span>'
            sigcls = "sig-gray"
            tag = r["status"] or "未开售"
        else:
            p = r["probs"]
            prob = (f'<span class="ph">{p[0]:.1f}</span> / <span class="ph">{p[1]:.1f}</span> / '
                    f'<span class="ph">{p[2]:.1f}</span>')
            best = f'{r["best"]}（{r["bestp"]:.1f}%）'
            d = r["diff"]
            diff = '<span class="muted">—</span>' if d is None else f'{"+" if d >= 0 else "−"}{abs(d):.1f}pp'
            rtp = f'{r["rtp"]:.1f}%'
            sigcls = cls(r["sig"])
            tag = r["sig"].split("·")[0]
        trs.append(f"""
      <tr>
        <td class="c-code">{esc(r['code'])}</td>
        <td class="c-league">{esc(r['league'])}</td>
        <td class="c-team"><div class="t1">{esc(r['home'])}</div><div class="vs">VS</div><div class="t2">{esc(r['away'])}</div></td>
        <td class="c-hcap">{esc(r['handicap'])}<div class="mk">{esc(r['mtype'])}</div></td>
        <td class="c-prob">{prob}</td>
        <td class="c-best">{best}</td>
        <td class="c-diff">{diff}</td>
        <td class="c-rtp">{rtp}</td>
        <td class="c-sig"><span class="sig {sigcls}">{tag}</span></td>
        <td class="c-status">{esc(r['status'])}</td>
      </tr>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>竞彩赛事分析台账 {esc(meta.get('batch',''))}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#eef1f5; font-family:'Noto Sans CJK SC','Noto Sans CJK JP','Source Han Sans SC',sans-serif; }}
  .page {{ width:1140px; margin:0 auto; background:#fff; }}
  .head {{ background:#132a52; color:#fff; padding:26px 34px 18px; }}
  .head h1 {{ margin:0 0 12px; font-size:27px; letter-spacing:.5px; font-weight:700; }}
  .meta {{ font-size:12.5px; color:#c8d3e6; line-height:1.9; }}
  .meta b {{ color:#f0d9a8; font-weight:600; }}
  .kpis {{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; padding:20px 32px 6px; }}
  .kpi {{ border:1px solid #dfe5ee; border-radius:10px; padding:16px 8px 14px; text-align:center; background:#fbfcfe; }}
  .kpi .n {{ font-size:34px; font-weight:700; color:#132a52; line-height:1.1; }}
  .kpi .n.g {{ color:#159c6b; }} .kpi .n.o {{ color:#d98b1f; }}
  .kpi .l {{ font-size:12px; color:#7b879b; margin-top:8px; }}
  .banner {{ margin:16px 32px 14px; background:#fdf6e3; border-left:4px solid #e8c06a; border-radius:6px; padding:14px 18px; font-size:12.5px; color:#5d4b22; line-height:1.85; }}
  .banner b {{ color:#a8791c; }}
  table {{ width:calc(100% - 64px); margin:0 32px; border-collapse:collapse; font-size:12.5px; table-layout:fixed; }}
  thead th {{ background:#e9eef7; color:#3c4a63; font-weight:700; padding:11px 8px; border-bottom:2px solid #d2dbe9; }}
  thead th small {{ display:block; font-weight:400; color:#7b879b; font-size:11px; margin-top:3px; }}
  tbody td {{ padding:10px 6px; border-bottom:1px solid #eceff4; text-align:center; color:#3c4a63; }}
  tbody tr:nth-child(even) {{ background:#fafbfd; }}
  .t1 {{ font-weight:600; color:#1b2b47; }} .t2 {{ color:#4b5a74; }}
  .vs {{ font-size:10.5px; color:#a7b1c2; margin:3px 0; letter-spacing:1px; }}
  .c-code {{ font-weight:600; color:#132a52; }}
  .c-hcap {{ font-weight:600; color:#132a52; }}
  .mk {{ font-size:10.5px; color:#93a0b5; font-weight:400; margin-top:3px; }}
  .ph {{ font-weight:600; color:#132a52; }}
  .c-best {{ font-weight:600; color:#1b2b47; }}
  .sig {{ display:inline-block; padding:3px 9px; border-radius:20px; font-size:11.5px; font-weight:600; }}
  .sig-green {{ background:#e6f6ee; color:#159c6b; }}
  .sig-orange {{ background:#fdf0dc; color:#d98b1f; }}
  .sig-gray {{ background:#eef1f6; color:#8a95a8; }}
  .muted {{ color:#aab3c2; }}
  .cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; padding:22px 32px 8px; }}
  .card {{ background:#fbfcfe; border:1px solid #dfe5ee; border-radius:10px; padding:16px 18px; }}
  .card h4 {{ margin:0 0 8px; font-size:13.5px; color:#132a52; }}
  .card p {{ margin:0; font-size:12px; color:#6b7789; line-height:1.85; }}
  .foot {{ margin:20px 0 0; background:#132a52; color:#dfe6f2; padding:22px 32px 16px; }}
  .foot .warn {{ text-align:center; font-size:13.5px; font-weight:600; color:#f3d68f; }}
  .foot .sub {{ text-align:center; font-size:12px; color:#a9b6cc; margin-top:9px; }}
  .strip {{ background:#0e2144; color:#8fa0bd; font-size:11.5px; padding:10px 32px; display:flex; justify-content:space-between; }}
</style></head><body><div class="page">
  <div class="head">
    <h1>竞彩足球 · 当日开售赛事分析台账快照</h1>
    <div class="meta">期号：<b>{esc(meta.get('batch',''))}</b>　|　数据源：<b>{esc(meta.get('source',''))}</b>　|　概率口径：<b>赔率去水归一化</b>　|　赔率更新：<b>{esc(meta.get('odds_update_time',''))}</b></div>
    <div class="meta">字段：主胜 / 平 / 客胜＝去水隐含概率（%）　·　偏差＝该盘最高概率项概率 − 官方公开支持率　·　RTP＝理论返还率</div>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="n">{matches}</div><div class="l">当日开售场次</div></div>
    <div class="kpi"><div class="n">{len(sold)}</div><div class="l">在售盘口样本</div></div>
    <div class="kpi"><div class="n o">{len(high)}</div><div class="l">最高项概率 ≥60%</div></div>
    <div class="kpi"><div class="n g">{len(green)}</div><div class="l">共识信号（绿）</div></div>
    <div class="kpi"><div class="n o">{len(orange)}</div><div class="l">分歧信号（橙）</div></div>
  </div>
  <div class="banner"><b>口径说明：</b>去水概率＝(1/赔率) ÷ Σ(1/赔率)，剔除博彩公司抽水；支持率为官方公开投注人数占比。<b>信号仅衡量赔率所定概率与群众实际投注热度之间的背离</b>，不包含任何胜平负预测；背离越大，说明市场定价与大众情绪分歧越大，仅作复盘观察指标。</div>
  <table>
    <thead><tr>
      <th style="width:70px">编号</th><th style="width:64px">联赛</th><th style="width:182px">对阵</th>
      <th style="width:120px">玩法／让球</th><th style="width:158px">去水概率 主/平/客<small>单位：%</small></th>
      <th style="width:142px">概率最高项<small>及该盘概率</small></th><th style="width:90px">概率−支持率</th>
      <th style="width:74px">返还率</th><th style="width:58px">信号</th><th style="width:96px">状态</th>
    </tr></thead>
    <tbody>{''.join(trs)}</tbody>
  </table>
  <div class="cards">
    <div class="card"><h4>返还率概览</h4><p>本批在售盘口理论返还率均值约 <b>{avg_rtp:.1f}%</b>。返还率越高抽水越少、赔率越接近真实概率；长期结算期望为负，台账只做概率与热度对照记录。</p></div>
    <div class="card"><h4>口径与置信度</h4><p>概率来自官方固定奖金反算，属静态快照；赔率随投注实时浮动，以出票时刻为准。支持率为人数占比、非金额占比，存在样本偏差，越临近开赛越接近真实倾向。</p></div>
    <div class="card"><h4>标注规则</h4><p><b>绿·共识</b>＝最高项概率≥60% 且 偏差≥−5pp；<b>橙·分歧</b>＝最高项概率≥60% 但偏差&lt;−5pp（热度明显高于赔率概率）；<b>灰</b>＝无 ≥50%/60% 强势项或未开盘。</p></div>
  </div>
  <div class="foot">
    <div class="warn">⚠ 仅数据统计展示，不构成购彩建议，不预测赛果；合法购彩仅限线下实体门店</div>
    <div class="sub">本快照为分析台账留存，用于赛后偏差比对：赔率、去水概率、支持率、返还率均为抓取时点固定值</div>
  </div>
  <div class="strip"><span>抓取时点：{esc(meta.get('odds_update_time',''))}　生成时点：{esc(meta.get('generated_at',''))}</span><span>台账：{esc(meta.get('batch',''))}　|　字段版本 v1.0</span></div>
</div></body></html>"""

def write_csv(rows, path):
    lines = ["编号,联赛,开赛时间,主队,客队,玩法,让球,主胜概率%,平%,客胜%,支持率主,支持率平,支持率客,概率最高项,最高项概率%,偏差pp,返还率%,信号,状态"]
    for r in rows:
        if not r["probs"]:
            lines.append(f'{r["code"]},{r["league"]},{r["kickoff"]},{r["home"]},{r["away"]},{r["mtype"]},{r["handicap"]},,,,,,,,,,,,{r["status"]}')
            continue
        p, s = r["probs"], r["support"] or [None]*3
        lines.append(f'{r["code"]},{r["league"]},{r["kickoff"]},{r["home"]},{r["away"]},{r["mtype"]},{r["handicap"]},'
                     f'{p[0]:.2f},{p[1]:.2f},{p[2]:.2f},{s[0]},{s[1]},{s[2]},{r["best"]},{r["bestp"]:.2f},'
                     f'{r["diff"]:+.2f},{r["rtp"]:.2f},{r["sig"]},{r["status"]}')
    path.write_text("\n".join(lines), encoding="utf-8")

BROWSER_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    "/usr/local/bin/chromium",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

def find_browser():
    """返回本机可用的浏览器可执行文件路径；找不到返回 None"""
    for c in BROWSER_CANDIDATES:
        if c and pathlib.Path(c).exists():
            return c
    return None

def trim_bottom_blank(png_path):
    """裁剪截图底部纯色空白（无 Pillow 时跳过）"""
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    px = im.load()
    bg = px[w // 2, h - 1]
    last = h - 1
    while last > 0:
        row_mid = px[w // 2, last]
        row_left = px[2, last]
        if row_mid != bg or row_left != bg:
            break
        last -= 1
    if last < h - 1:
        im.crop((0, 0, w, min(h, last + 1))).save(png_path)

async def render_png(html_path, png_path):
    exe = find_browser()
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        async_playwright = None

    if async_playwright is not None:
        async with async_playwright() as pw:
            kw = {"args": ["--no-sandbox"]}
            if exe:
                kw["executable_path"] = exe
            b = await pw.chromium.launch(**kw)
            pg = await b.new_page(viewport={"width": 1140, "height": 900}, device_scale_factor=2)
            await pg.goto(html_path.as_uri())
            await pg.wait_for_timeout(500)
            await pg.screenshot(path=str(png_path), full_page=True)
            await b.close()
        return

    if not exe:
        raise RuntimeError("未找到可用的 Chrome/Edge/Chromium，且未安装 playwright，无法渲染 PNG")
    subprocess.run(
        [exe, "--headless", "--disable-gpu", "--hide-scrollbars",
         f"--screenshot={png_path}", "--window-size=1140,2600", html_path.as_uri()],
        check=True,
    )
    trim_bottom_blank(png_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="赛事 JSON 文件路径")
    ap.add_argument("--out", required=True, help="输出目录")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    meta = data.get("meta", {})
    rows = build_rows(data.get("match_list", []))

    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    batch = meta.get("batch", "ledger")

    html_path = out / f"台账_{batch}.html"
    csv_path = out / f"台账_{batch}.csv"
    png_path = out / f"台账_{batch}.png"

    html_path.write_text(render_html(meta, rows), encoding="utf-8")
    write_csv(rows, csv_path)
    asyncio.run(render_png(html_path, png_path))
    print(f"HTML: {html_path}\nCSV: {csv_path}\nPNG: {png_path}\nrows: {len(rows)}")

if __name__ == "__main__":
    main()
