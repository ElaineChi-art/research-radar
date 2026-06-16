# -*- coding: utf-8 -*-
"""把每日聚合結果組成 HTML 研究雷達。"""
import html
import json

GRAPH_JS = r"""
const GRAPHS = /*GRAPHS*/;
const built = {};
function buildGraph(id){
  if (built[id] || !window.vis) return; built[id] = true;
  const g = GRAPHS[id]; const el = document.getElementById('g_' + id);
  if (!g || !el) return;
  const nodes = g.nodes.map(n => n.group === 'concept'
    ? {id:n.id, label:n.label, shape:'box', color:{background:'#2a1f3a', border:'#9a6cff'},
       font:{color:'#d6c8ff', size:15}}
    : {id:n.id, label:n.label, shape:'dot', size:8,
       color:{background:'#7fb5ff', border:'#3a6ea5'}, font:{color:'#aeb6c2', size:11},
       url:n.url, title:n.title});
  const data = {nodes:new vis.DataSet(nodes),
                edges:new vis.DataSet(g.edges.map(e => ({from:e.from, to:e.to, color:'#2a3340'})))};
  const net = new vis.Network(el, data, {
    physics:{stabilization:true, barnesHut:{springLength:120, gravitationalConstant:-4000}},
    interaction:{hover:true}, nodes:{borderWidth:1}});
  net.on('click', p => { if (p.nodes.length){ const n = data.nodes.get(p.nodes[0]);
    if (n && n.url) window.open(n.url, '_blank'); }});
}
document.querySelectorAll('details.graphbox').forEach(d =>
  d.addEventListener('toggle', () => { if (d.open) buildGraph(d.querySelector('.graph').id.slice(2)); }));
"""

TAB_JS = r"""
document.querySelectorAll('.tabs .tab').forEach(function(b){
  b.addEventListener('click', function(){
    var sec = b.closest('.topic'), id = b.dataset.t;
    sec.querySelectorAll('.tab').forEach(function(x){ x.classList.toggle('on', x === b); });
    sec.querySelectorAll('.tabpanel').forEach(function(p){ p.classList.toggle('on', p.id === id); });
  });
});
"""


def _tags(tags):
    out = []
    for t in (tags or []):
        if isinstance(t, dict):
            out.append(f'<span class="kw c{t.get("ci",0)}">{html.escape(t.get("label",""))}</span>')
        else:
            out.append(f'<span class="kw">{html.escape(str(t))}</span>')
    return "".join(out)


def _item(it):
    new = '<span class="new">🆕 NEW</span>' if it.get("is_new") else ""
    date = f'<span class="date">{html.escape(it["date"])}</span>' if it.get("date") else ""
    meta = f'<span class="src">{html.escape(it["meta"])}</span>' if it.get("meta") else ""
    tags = f'<div class="kws">{_tags(it["tags"])}</div>' if it.get("tags") else ""
    summary = f'<p class="sum">{html.escape(it["summary"])}…</p>' if it.get("summary") else ""
    url = html.escape(it.get("url", "#"))
    return (f'<li><a href="{url}" target="_blank" rel="noopener">{html.escape(it["title"])}</a>'
            f'<div class="m">{new}{date}{meta}</div>{tags}{summary}</li>')


def _feed(items):
    if not items:
        return '<p class="empty">今日無新項目</p>'
    return f'<ul class="feed">{"".join(_item(i) for i in items)}</ul>'


def _judgments_block(t):
    if "judgments" not in t:
        return ""
    items = t.get("judgments", [])
    upd = t.get("judgments_updated", "")
    if not items:
        note = t.get("judgments_note") or "近期無命中關鍵字的新判決。"
        if "非本 API 服務時間" in note or "尚未" in note:
            note = "⏳ 判決全文將於每日台灣 00:00–06:00 由排程自動抓取並更新。"
        return ('<div class="judg"><h3>📜 司法院判決全文（金融／經濟犯罪）</h3>'
                f'<p class="empty">{html.escape(note)}</p></div>')
    rows = []
    for it in items:
        tags = _tags(it.get("tags") or it.get("keywords"))
        rows.append(
            f'<li><div class="jhead"><b>{html.escape(it.get("jtitle",""))}</b>'
            f'<span class="src">{html.escape(it.get("court",""))}　'
            f'{html.escape(it.get("no",""))}　{html.escape(it.get("date",""))}</span></div>'
            f'<div class="kws">{tags}</div>'
            f'<p class="sum">{html.escape(it.get("snippet",""))}…</p></li>'
        )
    return (f'<div class="judg"><h3>📜 司法院判決全文（金融／經濟犯罪）'
            f'<span class="src"> · 全文命中 {len(items)} 筆 · 更新 {html.escape(upd)}</span></h3>'
            f'<ul class="jfeed">{"".join(rows)}</ul></div>')


def _music_charts(t):
    c = t.get("charts")
    if not c or not c.get("index_table"):
        return ""
    tbl = ""
    for r in c.get("index_table", []):
        chg = r.get("chg_1y")
        cls = "up" if (chg or 0) >= 0 else "down"
        last = f'{r["last"]:.2f}' if r.get("last") is not None else "—"
        tbl += (f'<tr><td>{html.escape(r["name"])}<span class="src"> {html.escape(r["ticker"])}</span></td>'
                f'<td>{last}</td><td class="{cls}">{chg:+.1f}%</td></tr>')
    return f"""
      <div class="charts">
        <h3>📈 音樂 IP 金融指數 <span class="src">（Reservoir／Warner／Universal／Spotify，rebased 100）</span></h3>
        <div class="cgrid">
          <div><img src="assets/music_index.png" alt="index" loading="lazy"></div>
          <div><table class="ctab"><tr><th>標的</th><th>價格</th><th>近1年</th></tr>{tbl}</table></div>
        </div>
      </div>"""


GROUP_META = {"ip": {"name": "智財權（著作權・商標・專利）", "tag": "智財",
                     "desc": "台灣／AI／國際 三個面向 — 點上方切換"}}


def _topic_inner(t, graphs):
    cols = "".join(
        f'<div class="col"><h3>{html.escape(c["label"])}</h3>{_feed(c["items"])}</div>'
        for c in t.get("columns", [])
    )
    tid = t.get("id", "")
    graph_html = ""
    if t.get("graph") and t["graph"].get("nodes"):
        graphs[tid] = t["graph"]
        n = sum(1 for x in t["graph"]["nodes"] if x.get("group") == "item")
        graph_html = (f'<details class="graphbox"><summary>🕸 關聯圖（{n} 篇 × 概念節點，點節點開原文）</summary>'
                      f'<div class="graph" id="g_{html.escape(tid)}"></div></details>')
    return f'{_judgments_block(t)}{_music_charts(t)}<div class="cols">{cols}</div>{graph_html}'


def build_html(date_str, topics, generated_at):
    # 先把主題收斂成「單一主題」或「群組(分頁)」的呈現單元
    units, seen = [], set()
    for t in topics:
        g = t.get("group")
        if g:
            if g in seen:
                continue
            seen.add(g)
            units.append(("group", g, [x for x in topics if x.get("group") == g]))
        else:
            units.append(("single", t, None))

    sections, toc_items, graphs = [], [], {}
    for kind, a, members in units:
        if kind == "single":
            t = a
            area = t.get("area", "")
            cls = "tw" if area == "台灣" else "intl"
            tag = f'<span class="tag {cls}">{html.escape(area)}</span>' if area else ""
            tid = t.get("id", "")
            sections.append(
                f'<section class="topic" id="{html.escape(tid)}">'
                f'<h2>{tag}{html.escape(t["name"])} <span class="desc">{html.escape(t["desc"])}</span></h2>'
                f'{_topic_inner(t, graphs)}</section>')
            toc_items.append((tid, t["name"], cls))
        else:
            meta = GROUP_META.get(a, {"name": a, "tag": a, "desc": ""})
            tabs = "".join(
                f'<button class="tab{" on" if i == 0 else ""}" data-t="{a}-{i}">{html.escape(m["name"])}</button>'
                for i, m in enumerate(members))
            panels = "".join(
                f'<div class="tabpanel{" on" if i == 0 else ""}" id="{a}-{i}">{_topic_inner(m, graphs)}</div>'
                for i, m in enumerate(members))
            sections.append(
                f'<section class="topic group" id="{html.escape(a)}">'
                f'<h2><span class="tag intl">{html.escape(meta["tag"])}</span>{html.escape(meta["name"])} '
                f'<span class="desc">{html.escape(meta["desc"])}</span></h2>'
                f'<div class="tabs">{tabs}</div>{panels}</section>')
            toc_items.append((a, meta["name"], "intl"))

    body = "\n".join(sections)
    toc = "".join(
        f'<a href="#{html.escape(tid)}"><span class="d {cls}"></span>{html.escape(name)}</a>'
        for tid, name, cls in toc_items)
    graph_scripts = (
        '<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>'
        "<script>" + GRAPH_JS.replace("/*GRAPHS*/", json.dumps(graphs, ensure_ascii=False)) + "</script>"
    ) if graphs else ""
    graph_scripts += "<script>" + TAB_JS + "</script>"
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>研究雷達 · 台灣法律／智財／區塊鏈／AI · {date_str}</title>
<style>
  * {{ box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif;
         margin:0; background:#0c0e13; color:#e6e6e6; }}
  body::before {{ content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
    background:radial-gradient(1100px 560px at 75% -8%, rgba(70,100,180,.13), transparent 60%),
               radial-gradient(900px 520px at -5% 105%, rgba(130,70,160,.11), transparent 60%); }}
  .topnav {{ display:flex; gap:6px; background:#0b0d12; padding:8px 16px;
            border-bottom:1px solid #262b36; position:sticky; top:0; z-index:10; }}
  .topnav a {{ color:#9aa4b2; text-decoration:none; font-size:14px; font-weight:600;
              padding:7px 16px; border-radius:8px; }}
  .topnav a:hover {{ background:#161922; color:#e6e6e6; }}
  .topnav a.active {{ background:#1f2e3a; color:#7fb5ff; }}
  header {{ padding:26px 22px; background:linear-gradient(135deg,#1b2030,#13161d 70%);
           border-bottom:1px solid #262b36; }}
  header h1 {{ margin:0; font-size:23px; letter-spacing:.5px;
             background:linear-gradient(90deg,#cfe0ff,#e9d4ff); -webkit-background-clip:text;
             background-clip:text; color:transparent; }}
  header p {{ margin:6px 0 0; color:#9aa4b2; font-size:13px; }}
  .wrap {{ max-width:1320px; margin:0 auto; padding:18px 22px; }}
  /* 滑鼠移到左緣 → 目錄抽屜滑出 */
  .toc-trigger {{ position:fixed; left:0; top:50%; transform:translateY(-50%); z-index:40;
                 background:#161922; border:1px solid #2a3140; border-left:none;
                 border-radius:0 12px 12px 0; padding:16px 7px; cursor:pointer; color:#9aa4b2;
                 writing-mode:vertical-rl; letter-spacing:3px; font-size:12px; font-weight:600;
                 transition:.25s; box-shadow:4px 0 16px rgba(0,0,0,.3); }}
  .toc-trigger:hover {{ color:#fff; background:#1f2937; }}
  .toc-trigger .th {{ writing-mode:horizontal-tb; font-size:14px; }}
  .toc {{ position:fixed; left:0; top:48px; height:calc(100vh - 48px); width:252px; z-index:41;
         background:rgba(17,20,27,.96); backdrop-filter:blur(12px); border-right:1px solid #2a3140;
         padding:16px 14px; overflow:auto; transform:translateX(-100%);
         transition:transform .32s cubic-bezier(.4,0,.2,1); box-shadow:10px 0 40px rgba(0,0,0,.5); }}
  .toc-trigger:hover + .toc, .toc:hover {{ transform:translateX(0); }}
  .toctitle {{ font-size:12px; color:#7c8696; margin-bottom:10px; font-weight:600;
              letter-spacing:1px; }}
  .toc a {{ display:flex; align-items:center; gap:9px; color:#c3cad6; text-decoration:none;
           font-size:13.5px; padding:9px 10px; border-radius:9px; transition:.16s; }}
  .toc a:hover {{ background:#1f2937; color:#fff; transform:translateX(3px); }}
  .toc .d {{ width:8px; height:8px; border-radius:50%; flex:none; }}
  .toc .d.tw {{ background:#ff9ecb; }}
  .toc .d.intl {{ background:#7fb5ff; }}
  .topic {{ background:linear-gradient(180deg,#171b24,#13161d); border:1px solid #262b36;
           border-radius:14px; padding:20px; margin-bottom:18px; scroll-margin-top:64px;
           transition:transform .2s, box-shadow .25s, border-color .25s; animation:rise .5s both; }}
  .topic:hover {{ border-color:#39455f; box-shadow:0 14px 40px rgba(0,0,0,.4); }}
  @keyframes rise {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:none; }} }}
  .tabs {{ display:flex; gap:8px; flex-wrap:wrap; margin:4px 0 16px; }}
  .tab {{ background:#11151c; border:1px solid #2a3140; color:#9aa4b2; cursor:pointer;
         font-size:13.5px; font-weight:600; padding:8px 17px; border-radius:999px; transition:.18s; }}
  .tab:hover {{ color:#e6e6e6; border-color:#3a4660; transform:translateY(-1px); }}
  .tab.on {{ color:#fff; border-color:transparent; box-shadow:0 6px 18px rgba(80,90,255,.3);
            background:linear-gradient(135deg,#3a6ea5,#7c5cff); }}
  .tabpanel {{ display:none; animation:fade .28s; }}
  .tabpanel.on {{ display:block; }}
  @keyframes fade {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:none; }} }}
  .topic h2 {{ margin:0 0 14px; font-size:18px; }}
  .desc {{ color:#7c8696; font-size:13px; font-weight:normal; }}
  .tag {{ font-size:11px; font-weight:600; padding:2px 7px; border-radius:6px; margin-right:8px; }}
  .tag.tw {{ background:#3a2233; color:#ff9ecb; }}
  .tag.intl {{ background:#1f2e3a; color:#7fb5ff; }}
  .cols {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
  .col h3 {{ font-size:14px; color:#9aa4b2; margin:0 0 8px;
            border-bottom:1px solid #262b36; padding-bottom:6px; }}
  .feed {{ list-style:none; margin:0; padding:0; }}
  .feed li {{ margin:0 0 14px; font-size:13.5px; line-height:1.45; }}
  .feed a {{ color:#7fb5ff; text-decoration:none; transition:color .15s; }}
  .feed a:hover {{ color:#a9ccff; text-decoration:underline; }}
  .feed li {{ transition:transform .15s; }}
  .feed li:hover {{ transform:translateX(2px); }}
  .m {{ margin-top:3px; }}
  .new {{ background:#1f3a2a; color:#5ee0aa; font-size:10px; font-weight:700;
         padding:1px 6px; border-radius:5px; margin-right:6px; }}
  .date {{ color:#8a93a3; font-size:11px; margin-right:8px; }}
  .src {{ color:#7c8696; font-size:11px; }}
  .sum {{ color:#aeb6c2; font-size:12.5px; margin:5px 0 0; }}
  .kws {{ margin:5px 0 0; }}
  .kw {{ display:inline-block; background:#2a2233; color:#d6a9ff; font-size:11px;
        padding:1px 7px; border-radius:6px; margin:0 4px 4px 0; }}
  /* 六大犯罪類別配色：金融秩序/銀行/證券/公司/虛擬資產/詐欺 */
  .kw.c0 {{ background:#10263a; color:#7fc4ff; }}
  .kw.c1 {{ background:#0f3030; color:#6fe0d0; }}
  .kw.c2 {{ background:#3a2233; color:#ff9ecb; }}
  .kw.c3 {{ background:#2a2a12; color:#e6d36a; }}
  .kw.c4 {{ background:#2a1838; color:#c79cff; }}
  .kw.c5 {{ background:#3a1f18; color:#ffae8a; }}
  .empty {{ color:#6b7280; font-size:13px; }}
  .judg {{ background:#1a1410; border:1px solid #3a2a18; border-radius:10px;
          padding:14px; margin-bottom:14px; }}
  .judg h3 {{ margin:0 0 10px; font-size:15px; color:#ffcf99; }}
  .jfeed {{ list-style:none; margin:0; padding:0;
           display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }}
  .jfeed li {{ background:#161922; border:1px solid #262b36; border-radius:8px; padding:10px; }}
  .jhead b {{ font-size:14px; }}
  .jhead .src {{ display:block; color:#8a93a3; font-size:11px; margin-top:2px; }}
  .charts {{ background:#10171a; border:1px solid #1f3a3a; border-radius:10px;
            padding:14px; margin-bottom:14px; }}
  .charts h3 {{ margin:0 0 10px; font-size:15px; color:#9ee6d0; }}
  .cgrid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }}
  .charts img {{ width:100%; border-radius:8px; background:#fff; }}
  .ctab {{ width:100%; border-collapse:collapse; margin-top:8px; font-size:12.5px; }}
  .ctab th,.ctab td {{ text-align:left; padding:3px 6px; border-bottom:1px solid #222733; }}
  .ctab th {{ color:#7c8696; font-weight:600; }}
  .up {{ color:#36d399; }}
  .down {{ color:#ff5c5c; }}
  .ref {{ margin-top:8px; font-size:12px; color:#aeb6c2; }}
  .ref ul {{ margin:5px 0; padding-left:18px; }}
  .ref a {{ color:#7fb5ff; }}
  @media (max-width:980px) {{ .cgrid {{ grid-template-columns:1fr; }} }}
  .graphbox {{ margin-top:14px; }}
  .graphbox summary {{ cursor:pointer; color:#9ee6d0; font-size:14px; font-weight:600;
                      padding:6px 0; }}
  .graph {{ height:420px; border:1px solid #262b36; border-radius:10px;
           background:#0c0f14; margin-top:8px; }}
  footer {{ text-align:center; color:#6b7280; font-size:12px; padding:24px; }}
  @media (max-width:980px) {{ .cols,.jfeed {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<nav class="topnav">
  <a href="https://elainechi-art.github.io/taiwan-stock-dashboard/">📈 股市儀表板</a>
  <a class="active" href="https://elainechi-art.github.io/research-radar/">📡 研究雷達</a>
</nav>
<header>
  <h1>📡 研究雷達 · 台灣法律 / 智財 / 區塊鏈 / AI</h1>
  <p>資料日期：{date_str}　·　產生時間：{generated_at}　·　每日自動更新　·　🆕 = 近 7 天新資料</p>
</header>
<div class="toc-trigger" aria-hidden="true"><span class="th">☰</span><span class="tl">目錄</span></div>
<aside class="toc"><div class="toctitle">主題目錄</div>{toc}</aside>
<div class="wrap">
{body}
</div>
<footer>聚合 Google News、權威 RSS（DOJ/CFTC/Patently-O…）、Semantic Scholar、arXiv、CourtListener、司法院判決全文 · 供研究參考</footer>
{graph_scripts}
</body>
</html>"""
