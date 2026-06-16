# -*- coding: utf-8 -*-
"""音樂 IP 金融指標（WIPO 報告風格）：
  1) 版權基金/公司「價格指數」(yfinance) → docs/assets/music_index.png
  2) 「版權證券化」新聞熱度趨勢（每日累積）→ docs/assets/music_volume.png
  3) WIPO 報告引用之官方統計（靜態參考）
圖內文字用英文，避免 matplotlib 缺中文字型。
"""
import os
import json
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "docs", "assets")
DATA = os.path.join(ROOT, "docs", "data")

# 純度較高的上市音樂版權/版稅相關標的
INDEX_TICKERS = {"RSVR": "Reservoir Media", "WMG": "Warner Music",
                 "UMG.AS": "Universal Music", "SPOT": "Spotify"}

# WIPO WP99《Measuring IP Finance and Investment in the Music Industry》引用之官方統計
WIPO_REF = {
    "source": "WIPO Economic Research WP No. 99 (2026)",
    "url": "https://www.wipo.int/publications/en/details.jsp?id=4842",
    "stats": [
        '「音樂版權證券化」媒體報導：2014 年 56 篇 → 2024 年 450 篇',
        '美國著作權局：音樂版權移轉至 2020 年增加 65%',
        '音樂版權作為融資擔保品：自 2010 年近乎翻倍',
    ],
}


def build_index_chart():
    """畫等權重「音樂 IP 金融指數」(起點=100) + 各成分，回傳最新漲跌表。"""
    import yfinance as yf
    import pandas as pd
    os.makedirs(ASSETS, exist_ok=True)
    closes = {}
    for t in INDEX_TICKERS:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False, auto_adjust=False)
            if getattr(df.columns, "nlevels", 1) > 1:
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            s = df["close"].dropna()
            if len(s) > 20:
                closes[t] = s
        except Exception as e:
            print(f"  指數成分 {t} 失敗：{e}")
    if not closes:
        return []

    frame = pd.DataFrame(closes).ffill().dropna()
    norm = frame / frame.iloc[0] * 100.0
    index = norm.mean(axis=1)

    plt.figure(figsize=(9, 4.2))
    for t in norm.columns:
        plt.plot(norm.index, norm[t], linewidth=1, alpha=0.55, label=INDEX_TICKERS[t])
    plt.plot(index.index, index.values, color="#ff5ca8", linewidth=2.6,
             label="Music IP Finance Index (equal-wt)")
    plt.axhline(100, color="#888", linewidth=0.8, linestyle=":")
    plt.title("Music IP Finance Index — 1Y (rebased to 100)")
    plt.ylabel("Index (start = 100)")
    plt.legend(fontsize=8, loc="best")
    plt.xticks(rotation=30, fontsize=7)
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS, "music_index.png"), dpi=110)
    plt.close()

    table = []
    for t in norm.columns:
        last = float(frame[t].iloc[-1])
        chg = (norm[t].iloc[-1] - 100.0)
        table.append({"ticker": t, "name": INDEX_TICKERS[t], "last": round(last, 2),
                      "chg_1y": round(chg, 1)})
    table.append({"ticker": "INDEX", "name": "音樂 IP 金融指數", "last": None,
                  "chg_1y": round(float(index.iloc[-1] - 100.0), 1)})
    return table


def update_news_volume():
    """每日累積『版權證券化/版稅』相關新聞則數，畫成趨勢線。"""
    import sources
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, "music_news_volume.json")
    hist = []
    if os.path.exists(path):
        try:
            hist = json.load(open(path, encoding="utf-8"))
        except Exception:
            hist = []
    today = datetime.date.today().isoformat()
    q = '"music rights securitization" OR "music royalties" OR "catalog acquisition" OR "music IP fund"'
    try:
        count = len(sources.fetch_news(q, "en", 100))
    except Exception:
        count = 0
    hist = [h for h in hist if h.get("date") != today] + [{"date": today, "count": count}]
    hist.sort(key=lambda x: x["date"])
    json.dump(hist, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    plt.figure(figsize=(9, 3.2))
    xs = [h["date"] for h in hist]
    ys = [h["count"] for h in hist]
    plt.plot(xs, ys, color="#7fb5ff", marker="o", markersize=3)
    plt.fill_between(range(len(ys)), ys, color="#7fb5ff", alpha=0.15)
    plt.title("Music-rights news volume (daily, accumulating)")
    plt.ylabel("Articles / day")
    plt.xticks(rotation=30, fontsize=7)
    if len(xs) > 12:
        plt.gca().set_xticks(range(0, len(xs), max(1, len(xs) // 12)))
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS, "music_volume.png"), dpi=110)
    plt.close()
    return {"today": today, "count": count, "days": len(hist)}


def build():
    out = {"ref": WIPO_REF}
    try:
        out["index_table"] = build_index_chart()
    except Exception as e:
        print(f"指數圖失敗：{e}")
        out["index_table"] = []
    try:
        out["volume"] = update_news_volume()
    except Exception as e:
        print(f"新聞熱度圖失敗：{e}")
        out["volume"] = {}
    return out


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(build(), ensure_ascii=False, indent=2))
