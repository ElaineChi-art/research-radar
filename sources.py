# -*- coding: utf-8 -*-
"""資料源抓取器：Google News、RSS feeds、arXiv、Semantic Scholar、CourtListener。

全部免金鑰。每個函式回傳 list[dict]，欄位統一：
  {title, url, date, meta, summary, is_new}
摘要(summary)為「萃取式」：取來源本身的描述/摘要/全文前段（非 AI 生成）。
"""
import re
import json
import html as _html
import datetime
import urllib.parse
import urllib.request

UA = {"User-Agent": "research-radar/0.2 (academic research aggregator)"}
TODAY = datetime.date.today()
NEW_DAYS = 7  # 幾天內視為「新」


def _get_json(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _clean(text, limit=None):
    t = _html.unescape(re.sub(r"<[^>]+>", "", text or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:limit].rstrip() if limit and len(t) > limit else t)


def _parse_date(s):
    """回傳 (顯示字串 'YYYY-MM-DD', date物件或None)。"""
    if not s:
        return "", None
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            d = datetime.datetime.strptime(s, fmt)
            return d.strftime("%Y-%m-%d"), d.date()
        except ValueError:
            continue
    return s[:10], None


def _is_new(d):
    return bool(d and (TODAY - d).days <= NEW_DAYS)


def _entry_date(e):
    """從 feedparser entry 取得日期 date 物件。"""
    for k in ("published_parsed", "updated_parsed"):
        t = e.get(k)
        if t:
            try:
                return datetime.date(t.tm_year, t.tm_mon, t.tm_mday)
            except Exception:
                pass
    _, d = _parse_date(e.get("published", "") or e.get("updated", ""))
    return d


def _mk(title, url, d, meta, summary):
    ds = d.strftime("%Y-%m-%d") if d else ""
    return {"title": _clean(title), "url": url or "", "date": ds,
            "meta": _clean(meta), "summary": _clean(summary, 220), "is_new": _is_new(d),
            "_sort": ds or "0000-00-00"}


def fetch_news(query, lang="en", limit=6):
    import feedparser
    q = urllib.parse.quote(query)
    if lang == "zh":
        url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    else:
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    out = []
    for e in feed.entries[:limit]:
        src = e.get("source", {}).get("title", "") if e.get("source") else ""
        # Google News 的 summary 多為相關連結清單，萃取意義不大，留標題來源即可
        out.append(_mk(e.get("title"), e.get("link"), _entry_date(e), src, ""))
    return out


def fetch_rss(url, limit=6, source_name=""):
    """通用 RSS/Atom（權威部落格/官方新聞），用 entry 的描述做萃取式摘要。"""
    import feedparser
    feed = feedparser.parse(url, request_headers=UA)
    name = source_name or _clean(feed.feed.get("title", ""))
    out = []
    for e in feed.entries[:limit]:
        summary = e.get("summary", "") or (e.get("content", [{}])[0].get("value", "")
                                           if e.get("content") else "")
        out.append(_mk(e.get("title"), e.get("link"), _entry_date(e), name, summary))
    return out


def fetch_arxiv(query, limit=5):
    import feedparser
    cats = ("cat:cs.CY OR cat:cs.AI OR cat:cs.CR OR cat:cs.LG OR "
            "cat:cs.SI OR cat:cs.CL OR cat:cs.DC OR cat:econ.GN")
    full = f"({query}) AND ({cats})"
    url = ("http://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(full)
           + f"&sortBy=submittedDate&sortOrder=descending&max_results={limit}")
    feed = feedparser.parse(url)
    out = []
    for e in feed.entries[:limit]:
        authors = ", ".join(a.get("name", "") for a in e.get("authors", [])[:3])
        if len(e.get("authors", [])) > 3:
            authors += " et al."
        out.append(_mk(e.get("title"), e.get("link"), _entry_date(e),
                       "arXiv · " + authors, e.get("summary")))
    return out


def fetch_scholar(query, limit=5):
    """Semantic Scholar 論文搜尋（免金鑰），摘要用 abstract，連結點進論文頁。"""
    fields = "title,abstract,year,publicationDate,authors,url,externalIds,venue"
    url = ("https://api.semanticscholar.org/graph/v1/paper/search?query="
           + urllib.parse.quote(query) + f"&limit={limit}&fields={fields}")
    try:
        data = _get_json(url)
    except Exception:
        return []
    out = []
    for p in data.get("data", [])[:limit]:
        authors = ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:3])
        link = p.get("url") or ""
        doi = (p.get("externalIds") or {}).get("DOI")
        if doi:
            link = f"https://doi.org/{doi}"
        ds, d = _parse_date(p.get("publicationDate") or (str(p.get("year")) if p.get("year") else ""))
        meta = "Semantic Scholar · " + (authors or "") + (f" · {p.get('venue')}" if p.get("venue") else "")
        item = _mk(p.get("title"), link, d, meta, p.get("abstract") or "")
        item["date"] = ds or item["date"]
        item["_sort"] = item["date"] or "0000-00-00"
        out.append(item)
    return out


def fetch_courtlistener(query, limit=5):
    """CourtListener v4：以相關度抓較多筆，再依判決日期由新到舊排序取前 N。"""
    url = ("https://www.courtlistener.com/api/rest/v4/search/?q="
           + urllib.parse.quote(query) + "&type=o&order_by=score+desc")
    try:
        data = _get_json(url)
    except Exception:
        return []
    rows = []
    for r in data.get("results", [])[:25]:
        au = r.get("absolute_url", "")
        link = ("https://www.courtlistener.com" + au) if au.startswith("/") else au
        ds, d = _parse_date(r.get("dateFiled", ""))
        snip = ((r.get("opinions") or [{}])[0].get("snippet", "")) if r.get("opinions") else ""
        item = _mk(r.get("caseName"), link, d, r.get("court", ""), snip)
        item["date"] = ds or item["date"]
        item["_sort"] = item["date"] or "0000-00-00"
        rows.append(item)
    rows.sort(key=lambda x: x["_sort"], reverse=True)  # 由新到舊
    return rows[:limit]
