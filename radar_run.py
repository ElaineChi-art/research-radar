# -*- coding: utf-8 -*-
"""每日主程式：對每個主題聚合 新聞 + arXiv 論文 + 美國判決，產出研究雷達。

用法：python radar_run.py
輸出：docs/index.html、reports/<日期>.json
"""
import os
import json
import datetime
import traceback

import config
import sources
import report

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
REPORTS = os.path.join(ROOT, "reports")


def run():
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    topics = []
    for t in config.TOPICS:
        print(f"==> {t['name']}")
        kind = t.get("kind", "intl")
        data = {"id": t.get("id"), "name": t["name"], "desc": t["desc"], "kind": kind}
        try:
            if kind == "tw":
                # 台灣主題：三欄都來自中文新聞，不同查詢角度
                data["cols"] = [
                    {"label": c["label"],
                     "items": sources.fetch_news(c["q"], "zh", config.TW_COL_LIMIT)}
                    for c in t["cols"]
                ]
                print("    " + "　".join(f"{c['label']} {len(c['items'])}" for c in data["cols"]))
            else:
                data["news_en"] = sources.fetch_news(t["news_en"], "en", config.NEWS_EN_LIMIT)
                data["news_zh"] = sources.fetch_news(t["news_zh"], "zh", config.NEWS_ZH_LIMIT)
                data["papers"] = sources.fetch_arxiv(t["arxiv"], config.ARXIV_LIMIT)
                data["cases"] = sources.fetch_courtlistener(t["court"], config.COURT_LIMIT)
                print(f"    新聞 {len(data['news_en'])}+{len(data['news_zh'])}　"
                      f"論文 {len(data['papers'])}　判決 {len(data['cases'])}")
        except Exception as e:
            if kind == "tw":
                data.setdefault("cols", [])
            else:
                for k in ("news_en", "news_zh", "papers", "cases"):
                    data.setdefault(k, [])
            print(f"    ⚠️ {e}")
            traceback.print_exc()
        topics.append(data)

    # 掛上司法院判決全文（由 judicial.py 於台灣凌晨產生）
    jpath = os.path.join(DOCS, "data", "judgments.json")
    if os.path.exists(jpath):
        try:
            jdata = json.load(open(jpath, encoding="utf-8"))
            for d in topics:
                if d.get("id") == "tw-financial-crime":
                    d["judgments"] = jdata.get("items", [])
                    d["judgments_updated"] = jdata.get("updated", "")
                    d["judgments_note"] = jdata.get("note", "")
            print(f"判決全文：掛上 {len(jdata.get('items', []))} 筆")
        except Exception as e:
            print(f"讀取 judgments.json 失敗：{e}")

    html_str = report.build_html(today, topics, now)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_str)
    with open(os.path.join(REPORTS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

    total = sum(len(d["news_en"]) + len(d["news_zh"]) + len(d["papers"]) + len(d["cases"])
                for d in topics)
    print(f"\n完成：{len(topics)} 個主題、共 {total} 則項目 → docs/index.html")


if __name__ == "__main__":
    run()
