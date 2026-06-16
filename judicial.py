# -*- coding: utf-8 -*-
"""司法院裁判書全文監測（金融／經濟犯罪）。

流程：Auth（帳密→Token）→ JList（近7天異動清單）→ 用字別＋關鍵字粗篩
     → 只對命中的 jid 呼叫 JDoc 抓全文 → 再用關鍵字確認 → 存成 docs/data/judgments.json

注意：司法院 API 僅在台灣 00:00–06:00 提供服務，故本程式由 judicial.yml 排在該時段執行。
帳密來自環境變數 JUDICIAL_USER / JUDICIAL_PASS（存於 GitHub 加密 Secrets）。
"""
import os
import json
import time
import datetime
import urllib.request

import config

BASE = "https://data.judicial.gov.tw/jdg/api"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs", "data", "judgments.json")

# 字別粗篩（金融專業法庭常見字別）；全文再用 config 犯罪體系標籤比對
TARGET_PREFIX = ("金",)           # 金訴、金重訴、金上訴、金上重訴…
TARGET_EXACT = {"矚訴", "矚上訴", "矚重訴", "重訴"}
MAX_DOCS = 80                     # 單次最多抓幾篇全文，保護頻寬


def _post(path, payload, timeout=40):
    req = urllib.request.Request(
        f"{BASE}/{path}", method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": "research-radar/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def auth(user, pwd):
    d = _post("Auth", {"user": user, "password": pwd})
    if "Token" not in d:
        raise RuntimeError(f"驗證失敗：{d}")
    return d["Token"]


def jlist(token):
    """攤平回傳所有 jid（近7天異動）。"""
    d = _post("JList", {"token": token})
    jids = []
    for blk in (d if isinstance(d, list) else []):
        jids.extend(blk.get("list", []))
    return jids


def _ji(jid):
    """拆解 jid：法院,年度,字別,號次,日期,序。"""
    p = [x.strip() for x in jid.split(",")]
    return {"court": p[0], "year": p[1], "type": p[2], "no": p[3],
            "date": p[4] if len(p) > 4 else ""} if len(p) >= 4 else None


def prefilter(jids):
    """先用字別粗篩出金融／經濟犯罪可能相關的案件，避免抓全部全文。"""
    out = []
    for jid in jids:
        info = _ji(jid)
        if not info:
            continue
        z = info["type"]
        if z.startswith(TARGET_PREFIX) or z in TARGET_EXACT:
            out.append((jid, info))
    return out


def jdoc(token, jid):
    return _post("JDoc", {"token": token, "j": jid})


def run():
    user, pwd = os.environ.get("JUDICIAL_USER"), os.environ.get("JUDICIAL_PASS")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    result = {"updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
              "items": [], "note": ""}

    if not user or not pwd:
        result["note"] = "缺少 JUDICIAL_USER/JUDICIAL_PASS"
        _save(result)
        print(result["note"])
        return

    try:
        token = auth(user, pwd)
        jids = jlist(token)
        cand = prefilter(jids)
        print(f"異動 {len(jids)} 筆 → 字別粗篩命中 {len(cand)} 筆，逐筆抓全文…")

        items = []
        for jid, info in cand[:MAX_DOCS]:
            try:
                doc = jdoc(token, jid)
                full = (doc.get("JFULLX") or {}).get("JFULLCONTENT", "") or ""
                tags = config.tag_text(full)
                if not tags:
                    continue
                snippet = full.replace("\r", "").replace("\n", " ").strip()
                items.append({
                    "court": info["court"],
                    "jtitle": doc.get("JTITLE", ""),
                    "no": f'{info["year"]}年度{info["type"]}字第{info["no"]}號',
                    "date": info["date"],
                    "tags": tags,
                    "snippet": snippet[:300],
                })
            except Exception as e:
                print(f"  JDoc 失敗 {jid}: {e}")
            time.sleep(0.3)  # 對伺服器友善

        result["items"] = items
        result["scanned"] = len(jids)
        result["matched"] = len(items)
        print(f"完成：{len(items)} 筆命中關鍵字 → {OUT}")
    except Exception as e:
        result["note"] = f"執行失敗：{e}"
        print(result["note"])

    _save(result)


def _save(result):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()
