# -*- coding: utf-8 -*-
"""把每日聚合結果組成 HTML 研究雷達（給 GitHub Pages 用）。"""
import html


def _items(items, show_summary=False):
    if not items:
        return '<p class="empty">今日無新項目</p>'
    li = []
    for it in items:
        date = f'<span class="date">{html.escape(it["date"])}</span>' if it.get("date") else ""
        meta = f'<span class="src">{html.escape(it["meta"])}</span>' if it.get("meta") else ""
        summary = (f'<p class="sum">{html.escape(it["summary"])}…</p>'
                   if show_summary and it.get("summary") else "")
        url = html.escape(it.get("url", "#"))
        li.append(
            f'<li><a href="{url}" target="_blank" rel="noopener">{html.escape(it["title"])}</a>'
            f'<div class="m">{date}{meta}</div>{summary}</li>'
        )
    return f'<ul class="feed">{"".join(li)}</ul>'


def _judgments_block(t):
    """司法院判決全文區塊（只有金融犯罪主題、且有資料時才顯示）。"""
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
        kw = "".join(f'<span class="kw">{html.escape(k)}</span>' for k in it.get("keywords", []))
        rows.append(
            f'<li><div class="jhead"><b>{html.escape(it.get("jtitle",""))}</b>'
            f'<span class="src">{html.escape(it.get("court",""))}　'
            f'{html.escape(it.get("no",""))}　{html.escape(it.get("date",""))}</span></div>'
            f'<div class="kws">{kw}</div>'
            f'<p class="sum">{html.escape(it.get("snippet",""))}…</p></li>'
        )
    return (f'<div class="judg"><h3>📜 司法院判決全文（金融／經濟犯罪）'
            f'<span class="src"> · 全文比對命中 {len(items)} 筆 · 更新 {html.escape(upd)}</span></h3>'
            f'<ul class="jfeed">{"".join(rows)}</ul></div>')


def build_html(date_str, topics, generated_at):
    """topics: list of dict，每個含 name/desc 與 news/papers/cases。"""
    sections = []
    for t in topics:
        judg = _judgments_block(t)
        if t.get("kind") == "tw":
            tag = '<span class="tag tw">台灣</span>'
            cols = "".join(
                f'<div class="col"><h3>{html.escape(c["label"])}</h3>{_items(c["items"])}</div>'
                for c in t.get("cols", [])
            )
        else:
            tag = '<span class="tag intl">國際</span>'
            cols = (
                f'<div class="col"><h3>📰 新聞（中・英）</h3>'
                f'{_items(t["news_en"] + t["news_zh"])}</div>'
                f'<div class="col"><h3>📄 最新論文 · arXiv</h3>'
                f'{_items(t["papers"], show_summary=True)}</div>'
                f'<div class="col"><h3>⚖️ 美國判決 · CourtListener</h3>'
                f'{_items(t["cases"], show_summary=True)}</div>'
            )
        sections.append(f"""
        <section class="topic">
          <h2>{tag}{html.escape(t['name'])} <span class="desc">{html.escape(t['desc'])}</span></h2>
          {judg}
          <div class="cols">{cols}</div>
        </section>""")
    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>研究雷達 · 台灣法律／智財／區塊鏈／AI · {date_str}</title>
<style>
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif;
         margin:0; background:#0f1115; color:#e6e6e6; }}
  header {{ padding:24px 20px; background:#161922; border-bottom:1px solid #262b36; }}
  header h1 {{ margin:0; font-size:22px; }}
  header p {{ margin:6px 0 0; color:#9aa4b2; font-size:13px; }}
  .wrap {{ max-width:1280px; margin:0 auto; padding:20px; }}
  .topic {{ background:#161922; border:1px solid #262b36; border-radius:12px;
           padding:18px; margin-bottom:18px; }}
  .topic h2 {{ margin:0 0 14px; font-size:18px; }}
  .desc {{ color:#7c8696; font-size:13px; font-weight:normal; }}
  .tag {{ font-size:11px; font-weight:600; padding:2px 7px; border-radius:6px;
         margin-right:8px; vertical-align:middle; }}
  .tag.tw {{ background:#3a2233; color:#ff9ecb; }}
  .tag.intl {{ background:#1f2e3a; color:#7fb5ff; }}
  .cols {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
  .col h3 {{ font-size:14px; color:#9aa4b2; margin:0 0 8px;
            border-bottom:1px solid #262b36; padding-bottom:6px; }}
  .feed {{ list-style:none; margin:0; padding:0; }}
  .feed li {{ margin:0 0 12px; font-size:13.5px; line-height:1.4; }}
  .feed a {{ color:#7fb5ff; text-decoration:none; }}
  .feed a:hover {{ text-decoration:underline; }}
  .m {{ margin-top:3px; }}
  .date {{ color:#5ee0aa; font-size:11px; margin-right:8px; }}
  .src {{ color:#7c8696; font-size:11px; }}
  .sum {{ color:#aab3c0; font-size:12px; margin:5px 0 0; }}
  .empty {{ color:#6b7280; font-size:13px; }}
  .judg {{ background:#1a1410; border:1px solid #3a2a18; border-radius:10px;
          padding:14px; margin-bottom:14px; }}
  .judg h3 {{ margin:0 0 10px; font-size:15px; color:#ffcf99; }}
  .jfeed {{ list-style:none; margin:0; padding:0;
           display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }}
  .jfeed li {{ background:#161922; border:1px solid #262b36; border-radius:8px; padding:10px; }}
  .jhead b {{ font-size:14px; }}
  .jhead .src {{ display:block; color:#8a93a3; font-size:11px; margin-top:2px; }}
  .kws {{ margin:6px 0; }}
  .kw {{ display:inline-block; background:#3a2233; color:#ff9ecb; font-size:11px;
        padding:1px 7px; border-radius:6px; margin:0 4px 4px 0; }}
  @media (max-width:880px) {{ .jfeed {{ grid-template-columns:1fr; }} }}
  footer {{ text-align:center; color:#6b7280; font-size:12px; padding:24px; }}
  @media (max-width:880px) {{ .cols {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>📡 研究雷達 · 台灣法律 / 智財 / 區塊鏈 / AI</h1>
  <p>資料日期：{date_str}　·　產生時間：{generated_at}　·　每日自動更新　·　來源：Google News、arXiv、CourtListener</p>
</header>
<div class="wrap">
{body}
</div>
<footer>每日自動聚合學術論文、國際新聞與美國判決 · 供研究參考</footer>
</body>
</html>"""
