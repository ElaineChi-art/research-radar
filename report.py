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


def build_html(date_str, topics, generated_at):
    """topics: list of dict，每個含 name/desc 與 news/papers/cases。"""
    sections = []
    for t in topics:
        news = t["news_en"] + t["news_zh"]
        sections.append(f"""
        <section class="topic">
          <h2>{html.escape(t['name'])} <span class="desc">{html.escape(t['desc'])}</span></h2>
          <div class="cols">
            <div class="col">
              <h3>📰 新聞（中・英）</h3>
              {_items(news)}
            </div>
            <div class="col">
              <h3>📄 最新論文 · arXiv</h3>
              {_items(t['papers'], show_summary=True)}
            </div>
            <div class="col">
              <h3>⚖️ 美國判決 · CourtListener</h3>
              {_items(t['cases'], show_summary=True)}
            </div>
          </div>
        </section>""")
    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>研究雷達 · 智財／區塊鏈／AI · {date_str}</title>
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
  footer {{ text-align:center; color:#6b7280; font-size:12px; padding:24px; }}
  @media (max-width:880px) {{ .cols {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>📡 研究雷達 · 智財 / 區塊鏈 / AI</h1>
  <p>資料日期：{date_str}　·　產生時間：{generated_at}　·　每日自動更新　·　來源：Google News、arXiv、CourtListener</p>
</header>
<div class="wrap">
{body}
</div>
<footer>每日自動聚合學術論文、國際新聞與美國判決 · 供研究參考</footer>
</body>
</html>"""
