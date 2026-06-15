# -*- coding: utf-8 -*-
"""三個資料源的抓取器：Google News、arXiv、CourtListener。

全部用免費、免金鑰的公開端點。每個函式回傳 list[dict]，欄位統一：
  {title, url, date, meta, summary}
"""
import re
import json
import datetime
import urllib.parse
import urllib.request

UA = {"User-Agent": "research-radar/0.1 (academic use)"}


def _get_json(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _clean(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text or "")).strip()


def _fmt_date(s):
    """把各種日期字串統一成 YYYY-MM-DD（抓不到就原樣回傳前 10 字）。"""
    if not s:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s[:10]


def fetch_news(query, lang="en", limit=6):
    """Google News RSS（lang: 'en' 英文 / 'zh' 中文）。"""
    import feedparser
    q = urllib.parse.quote(query)
    if lang == "zh":
        url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    else:
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    out = []
    for e in feed.entries[:limit]:
        out.append({
            "title": _clean(e.get("title")),
            "url": e.get("link", ""),
            "date": _fmt_date(e.get("published", "")),
            "meta": _clean(e.get("source", {}).get("title", "")) if e.get("source") else "",
            "summary": "",
        })
    return out


def fetch_arxiv(query, limit=5):
    """arXiv API（依投稿日期排序，回傳最新論文）。"""
    import feedparser
    # 限制在資訊/經濟相關分類，避免物理等不相關論文誤入
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
        out.append({
            "title": _clean(e.get("title")),
            "url": e.get("link", ""),
            "date": _fmt_date(e.get("published", "")),
            "meta": authors,
            "summary": _clean(e.get("summary"))[:240],
        })
    return out


def fetch_courtlistener(query, limit=5):
    """CourtListener v4 搜尋 API（美國判決意見，依判決日期排序）。"""
    # 用相關度排序（而非單純最新），研究雷達看「最相關的近期判決」比較有用
    url = ("https://www.courtlistener.com/api/rest/v4/search/?q="
           + urllib.parse.quote(query)
           + "&type=o&order_by=score+desc")
    try:
        data = _get_json(url)
    except Exception:
        return []
    out = []
    for r in data.get("results", [])[:limit]:
        au = r.get("absolute_url", "")
        out.append({
            "title": _clean(r.get("caseName")),
            "url": ("https://www.courtlistener.com" + au) if au.startswith("/") else au,
            "date": _fmt_date(r.get("dateFiled", "")),
            "meta": _clean(r.get("court", "")),
            "summary": _clean((r.get("opinions") or [{}])[0].get("snippet", ""))[:240]
                       if r.get("opinions") else "",
        })
    return out
