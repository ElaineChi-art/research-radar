# -*- coding: utf-8 -*-
"""研究雷達設定檔。

每個 TOPIC 有若干 columns，每個 column 可從多個來源聚合：
  news_en / news_zh : Google News 查詢字串
  scholar           : Semantic Scholar 查詢字串
  arxiv             : arXiv 查詢字串
  court             : CourtListener 查詢字串（美國判決）
  rss               : [[url, 顯示名], ...]  權威部落格/官方新聞 RSS
聚合後依日期由新到舊排序，近 7 天標 🆕。
"""

COL_LIMIT = 8  # 每欄最多顯示幾則

# 經濟犯罪分類體系（依使用者 PPT 講義；大類→子類→關鍵字）
# 關鍵字為字串=子字串比對；為 list=該 list 內所有詞都要出現(AND)
CRIME_TAXONOMY = [
    ("金融秩序犯罪", [
        ("非法吸金", ["非法吸金", "違法吸金", "吸金", "違法吸收資金"]),
        ("地下匯兌", ["地下匯兌", "非法匯兌"]),
        ("非法買賣外匯", ["非法買賣外匯", "地下外匯", "違法外匯"]),
        ("洗錢", ["洗錢", "洗錢防制", "洗防"]),
    ]),
    ("銀行犯罪", [
        ("銀行職員背信", [["銀行", "背信"], ["行員", "背信"]]),
        ("詐欺銀行", ["詐貸", "詐取貸款", "騙貸", "詐欺銀行"]),
        ("掏空放款", ["掏空放款", "超貸", "違法放款"]),
    ]),
    ("證券犯罪", [
        ("內線交易", ["內線交易", "內部人交易"]),
        ("操縱股價", ["操縱股價", "炒股", "操縱市場", "護盤", "拉抬股價", "沖洗買賣"]),
        ("財報不實", ["財報不實", "不實財報", "財務報表不實", "美化財報", "作假帳"]),
        ("非法募集證券", ["非法募集", "違法募集", "未經核准募集"]),
    ]),
    ("公司犯罪", [
        ("特別背信", ["特別背信"]),
        ("掏空公司", ["掏空公司", "掏空資產", "掏空"]),
        ("侵占公司資產", ["侵占公司", "業務侵占", "侵占資產", "侵占"]),
    ]),
    ("虛擬資產犯罪", [
        ("NFT", ["NFT"]),
        ("虛擬貨幣吸金", [["虛擬", "吸金"], ["加密", "吸金"], ["虛擬通貨", "吸金"], ["幣圈", "吸金"]]),
        ("虛擬貨幣洗錢", [["虛擬", "洗錢"], ["加密", "洗錢"], ["虛擬通貨", "洗錢"]]),
        ("STO", ["STO", "證券型代幣"]),
    ]),
    ("詐欺型犯罪", [
        ("投資詐欺", ["投資詐欺", "假投資", "投資詐騙"]),
        ("龐氏騙局", ["龐氏", "老鼠會"]),
        ("多層次傳銷", ["多層次傳銷", "違法傳銷"]),
    ]),
]

# 大類短名與配色索引（給標籤上色，呈現體系感）
CAT_SHORT = {"金融秩序犯罪": "金融秩序", "銀行犯罪": "銀行", "證券犯罪": "證券",
             "公司犯罪": "公司", "虛擬資產犯罪": "虛擬資產", "詐欺型犯罪": "詐欺"}
CAT_INDEX = {cat: i for i, (cat, _) in enumerate(CRIME_TAXONOMY)}


# 關聯圖（Obsidian 風）每個主題的「概念節點」詞庫；金融犯罪主題沿用犯罪體系
GRAPH_CONCEPTS = {
    "tw-ip": [("著作權", ["著作權"]), ("商標", ["商標"]), ("專利", ["專利"]),
              ("侵權", ["侵權", "侵害"]), ("訴訟", ["訴訟", "判決", "法院"]),
              ("修法", ["修正", "三讀", "草案"])],
    "ai-ip": [("著作權", ["著作權", "copyright"]), ("商標", ["商標", "trademark"]),
              ("專利", ["專利", "patent"]), ("生成式AI", ["生成式", "generative", "llm", "gpt"]),
              ("訴訟", ["lawsuit", "訴訟", "court", "ruling", "infringement"]),
              ("訓練資料", ["training data", "訓練資料", "dataset", "fair use"])],
    "music-ip": [("NFT", ["nft"]), ("版稅", ["royalt", "版稅"]), ("著作權", ["copyright", "著作權"]),
                 ("區塊鏈", ["blockchain", "區塊鏈"]), ("智能合約", ["smart contract", "智能合約"]),
                 ("授權", ["licens", "授權"]), ("串流", ["streaming", "串流"]),
                 ("投資/基金", ["investment", "fund", "投資", "基金", "catalog"])],
    "blockchain-gov": [("DAO", ["dao", "decentralized autonomous"]), ("治理", ["governance", "治理"]),
                       ("智能合約", ["smart contract", "智能合約"]), ("鏈上", ["on-chain", "鏈上"]),
                       ("代幣", ["token", "代幣"]), ("監管/制裁", ["regulation", "監管", "sanction", "制裁"])],
    "ip-authority": [("專利", ["patent", "專利"]), ("訴訟", ["litigation", "court", "訴訟", "appeal"]),
                     ("中國", ["china", "中國", "chinese"]), ("USPTO", ["uspto"]),
                     ("著作權", ["copyright", "著作權"]), ("商標", ["trademark", "商標"])],
}


def concept_tags(topic_id, text):
    """回傳該文字命中的概念節點標籤（給關聯圖用）。"""
    if topic_id == "tw-financial-crime":
        return [t["sub"] for t in tag_text(text)]
    low = (text or "").lower()
    return [c for c, kws in GRAPH_CONCEPTS.get(topic_id, []) if any(k.lower() in low for k in kws)]


def _kw_match(text, kw):
    return all(t in text for t in kw) if isinstance(kw, (list, tuple)) else (kw in text)


def tag_text(text):
    """掃描文字，回傳命中的犯罪標籤 [{cat,sub,label,ci}]（label 形如『證券·內線交易』）。"""
    text = text or ""
    out, seen = [], set()
    for cat, subs in CRIME_TAXONOMY:
        for sub, kws in subs:
            if (cat, sub) in seen:
                continue
            if any(_kw_match(text, k) for k in kws):
                seen.add((cat, sub))
                out.append({"cat": cat, "sub": sub,
                            "label": f"{CAT_SHORT[cat]}·{sub}", "ci": CAT_INDEX[cat]})
    return out

# 權威 RSS（白領犯罪：DOJ/CFTC；國際智財：使用者提供之 feeds）
DOJ = ["https://www.justice.gov/news/rss?type=press_release", "DOJ 司法部"]
SEC = ["https://www.sec.gov/news/pressreleases.rss", "SEC 證管會"]
CFTC = ["https://www.cftc.gov/RSS/RSSGP/rssgp.xml", "CFTC 商品期貨"]
F_PATENTLYO = ["https://www.patentlyo.com/patent/atom.xml", "Patently-O"]
F_PATENTDOCS = ["https://www.patentdocs.org/atom.xml", "Patent Docs"]
F_IPWATCHDOG = ["https://ipwatchdog.com/feed/", "IPWatchdog"]
F_CPR = ["http://comparativepatentremedies.blogspot.com/feeds/posts/default", "Comparative Patent Remedies"]
F_IPFRAY = ["https://ipfray.com/feed", "ip fray"]
F_CHINAIPR = ["http://chinaipr.com/feed/", "China IPR"]
F_CHINACM = ["http://chinacopyrightandmedia.wordpress.com/feed/", "China Copyright & Media"]
F_JDSUPRA = ["http://www.jdsupra.com/resources/syndication/docsRSSFeed.aspx?ftype=IntellectualProperty", "JD Supra IP"]
F_IPFINANCE = ["http://www.ip.finance/feeds/posts/default", "IP Finance"]
F_ENPAN = ["http://enpan.blogspot.com/feeds/posts/default", "enpan Patent"]

TOPICS = [
    {
        "id": "tw-financial-crime",
        "name": "台灣經濟刑法",
        "desc": "白領／經濟犯罪：內線交易・背信・掏空・洗錢・銀行法・組織犯罪…（重金庭領域）",
        "area": "台灣", "crime_tags": True, "judgments": True,
        "columns": [
            {"label": "⚖️ 判決・起訴",
             "news_zh": '(內線交易 OR 操縱股價 OR 財報不實 OR 特別背信 OR 掏空 OR 非法吸金 OR 地下匯兌 OR 洗錢 OR 超貸 OR 背信 OR 投資詐欺 OR 龐氏 OR 多層次傳銷 OR 虛擬貨幣 OR STO) (判決 OR 起訴 OR 判刑)'},
            {"label": "📋 法規・修法",
             "news_zh": '(證券交易法 OR 洗錢防制法 OR 銀行法 OR 組織犯罪防制條例) (修正 OR 三讀 OR 草案)'},
            {"label": "🇺🇸 美國執法 DOJ／SEC／CFTC",
             "rss": [DOJ, SEC, CFTC]},
        ],
    },
    {
        "id": "tw-ip",
        "name": "台灣智財（著作權／商標／專利）",
        "desc": "三大領域各自蒐集（判決・侵權・修法）",
        "area": "台灣", "group": "ip",
        "columns": [
            {"label": "© 著作權",
             "news_zh": '著作權 (判決 OR 侵權 OR 訴訟 OR 修正 OR 智慧財產)'},
            {"label": "™ 商標",
             "news_zh": '商標 (判決 OR 侵權 OR 異議 OR 評定 OR 訴訟)'},
            {"label": "⚙ 專利",
             "news_zh": '專利 (判決 OR 侵權 OR 舉發 OR 無效 OR 智慧財產法院)'},
        ],
    },
    {
        "id": "ai-ip",
        "name": "AI 智財（著作權／商標／專利）",
        "desc": "生成式 AI 對三大智財領域的衝擊（國際＋台灣）",
        "area": "國際", "group": "ip",
        "columns": [
            {"label": "© AI 著作權",
             "news_en": '"AI copyright" OR "generative AI" copyright OR "AI-generated" copyright',
             "news_zh": 'AI 著作權 OR 生成式AI 著作權 OR AI 訓練資料 侵權'},
            {"label": "™ AI 商標",
             "news_en": '"AI" trademark (lawsuit OR ruling OR infringement)',
             "news_zh": 'AI 商標 OR 生成式AI 商標'},
            {"label": "⚙ AI 專利",
             "news_en": '"AI patent" OR "artificial intelligence" patent (USPTO OR ruling)',
             "news_zh": 'AI 專利 OR 人工智慧 專利',
             "rss": [F_PATENTDOCS]},
        ],
    },
    {
        "id": "music-ip",
        "name": "音樂智財與投資",
        "desc": "音樂 NFT・版稅・數位音樂授權・IP 金融（論文核心）",
        "area": "國際",
        "columns": [
            {"label": "📰 新聞（中・英）",
             "news_en": '"music NFT" OR "music royalties" OR "music copyright" OR "music IP"',
             "news_zh": '音樂 NFT OR 音樂版權 OR 版稅 OR 數位音樂授權',
             "rss": [F_IPFINANCE]},
            {"label": "📚 學術論文（NFT・版權・智能合約）",
             "scholar": 'music NFT copyright royalties blockchain smart contract licensing'},
            {"label": "⚖️ 美國判決",
             "court": '"music" AND "copyright"'},
        ],
    },
    {
        "id": "blockchain-gov",
        "name": "區塊鏈演算法治理",
        "desc": "DAO・on-chain governance・智能合約治理（論文範圍）",
        "area": "國際",
        "columns": [
            {"label": "📰 新聞（中・英）",
             "news_en": '"blockchain governance" OR "DAO governance" OR "on-chain governance"',
             "news_zh": '區塊鏈 治理 OR DAO OR 去中心化 治理'},
            {"label": "📚 學術論文",
             "scholar": 'blockchain governance DAO decentralized autonomous organization',
             "arxiv": 'all:"blockchain governance" OR all:"decentralized autonomous organization" OR all:"on-chain governance"'},
            {"label": "⚖️ 美國判決",
             "court": '"decentralized autonomous organization"'},
        ],
    },
    {
        "id": "ip-authority",
        "name": "國際智財・專利 權威來源",
        "desc": "專利實務、訴訟救濟、中國IP（你指定的權威 feeds）",
        "area": "國際", "group": "ip",
        "columns": [
            {"label": "📄 專利實務",
             "rss": [F_PATENTLYO, F_PATENTDOCS, F_ENPAN]},
            {"label": "⚖️ 訴訟・救濟",
             "rss": [F_IPWATCHDOG, F_CPR, F_IPFRAY]},
            {"label": "🌏 中國IP・綜合",
             "rss": [F_CHINAIPR, F_CHINACM, F_JDSUPRA]},
        ],
    },
]
