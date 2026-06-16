# -*- coding: utf-8 -*-
"""每日主程式：依 config 的主題/欄位聚合多來源，產出研究雷達。"""
import os
import json
import time
import datetime
import traceback

import config
import sources
import report

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
REPORTS = os.path.join(ROOT, "reports")


def tag_crimes(text):
    text = text or ""
    return [label for label, kws in config.CRIME_TAGS if any(k in text for k in kws)]


def gather_column(col):
    """把一個欄位的所有來源抓回、合併、依日期由新到舊、去重、截斷。"""
    items = []
    try:
        if col.get("news_en"):
            items += sources.fetch_news(col["news_en"], "en", 6)
        if col.get("news_zh"):
            items += sources.fetch_news(col["news_zh"], "zh", 6)
        if col.get("scholar"):
            items += sources.fetch_scholar(col["scholar"], 5)
        if col.get("arxiv"):
            items += sources.fetch_arxiv(col["arxiv"], 4)
        if col.get("court"):
            items += sources.fetch_courtlistener(col["court"], 5)
        for rss in col.get("rss", []):
            url, name = rss[0], (rss[1] if len(rss) > 1 else "")
            try:
                items += sources.fetch_rss(url, 5, name)
            except Exception as e:
                print(f"     RSS 失敗 {name}: {e}")
            time.sleep(0.2)
    except Exception as e:
        print(f"    欄位來源失敗：{e}")
    # 去重（同標題）＋ 依日期新到舊
    seen, uniq = set(), []
    for it in items:
        key = it["title"][:60]
        if key and key not in seen:
            seen.add(key)
            uniq.append(it)
    uniq.sort(key=lambda x: x.get("_sort", ""), reverse=True)
    return uniq[:config.COL_LIMIT]


def run():
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    topics = []
    for t in config.TOPICS:
        print(f"==> {t['name']}")
        data = {"id": t.get("id"), "name": t["name"], "desc": t["desc"],
                "area": t.get("area", ""), "columns": []}
        for col in t.get("columns", []):
            items = gather_column(col)
            if t.get("crime_tags"):
                for it in items:
                    it["tags"] = tag_crimes(it["title"] + " " + it.get("summary", ""))
            data["columns"].append({"label": col["label"], "items": items})
            print(f"    {col['label']}: {len(items)}")
        topics.append((t, data))

    # 司法院判決全文
    jpath = os.path.join(DOCS, "data", "judgments.json")
    jdata = {}
    if os.path.exists(jpath):
        try:
            jdata = json.load(open(jpath, encoding="utf-8"))
            for it in jdata.get("items", []):
                it["tags"] = tag_crimes((it.get("jtitle", "") + " " + it.get("snippet", "")))
        except Exception as e:
            print(f"讀 judgments.json 失敗：{e}")
    # 音樂 IP 金融圖表
    mcharts = {}
    try:
        import music_charts
        mcharts = music_charts.build()
        print(f"音樂圖表：指數 {len(mcharts.get('index_table', []))} 成分、"
              f"新聞熱度 {mcharts.get('volume', {}).get('count', '—')}")
    except Exception as e:
        print(f"音樂圖表失敗：{e}")

    out_topics = []
    for t, data in topics:
        if t.get("judgments"):
            data["judgments"] = jdata.get("items", [])
            data["judgments_updated"] = jdata.get("updated", "")
            data["judgments_note"] = jdata.get("note", "")
        if t.get("id") == "music-ip" and mcharts:
            data["charts"] = mcharts
        out_topics.append(data)

    html_str = report.build_html(today, out_topics, now)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_str)
    with open(os.path.join(REPORTS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(out_topics, f, ensure_ascii=False, indent=2)

    total = sum(len(c["items"]) for d in out_topics for c in d["columns"])
    print(f"\n完成：{len(out_topics)} 主題、{total} 則 → docs/index.html")


if __name__ == "__main__":
    run()
