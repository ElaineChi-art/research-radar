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

COL_LIMIT = 6  # 每欄最多顯示幾則

# 金融／經濟犯罪分類標籤（掃描標題＋摘要自動標記；之後可依 PPT 增刪）
CRIME_TAGS = [
    ("內線交易", ["內線交易"]),
    ("操縱股價", ["操縱股價", "炒股", "操縱市場", "護盤", "拉抬股價"]),
    ("證券詐欺", ["證券詐欺", "證券交易法", "證交法"]),
    ("財報不實", ["財報不實", "不實財報", "財務報表不實", "美化財報"]),
    ("特別背信", ["特別背信"]),
    ("背信", ["背信"]),
    ("掏空", ["掏空"]),
    ("侵占", ["侵占", "業務侵占"]),
    ("洗錢", ["洗錢", "洗錢防制", "洗防"]),
    ("違法吸金／銀行法", ["違法吸金", "非法吸金", "吸金", "銀行法", "收受存款"]),
    ("詐欺", ["詐欺", "詐騙", "假投資"]),
    ("組織犯罪", ["組織犯罪", "犯罪組織"]),
    ("地下匯兌", ["地下匯兌", "非法匯兌"]),
    ("虛擬資產", ["虛擬資產", "虛擬通貨", "加密貨幣", "穩定幣"]),
    ("偽造文書", ["偽造文書"]),
]

# 權威 RSS（白領犯罪：DOJ/CFTC；國際智財：使用者提供之 feeds）
DOJ = ["https://www.justice.gov/feeds/opa/justice-news.xml", "DOJ"]
CFTC = ["https://www.cftc.gov/RSS/RSSGP/rssgp.xml", "CFTC"]
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
        "name": "台灣金融／經濟犯罪",
        "desc": "白領／經濟犯罪：內線交易・背信・掏空・洗錢・銀行法・組織犯罪…（重金庭領域）",
        "area": "台灣", "crime_tags": True, "judgments": True,
        "columns": [
            {"label": "⚖️ 判決・起訴",
             "news_zh": '(內線交易 OR 背信 OR 掏空 OR 證券詐欺 OR 洗錢 OR 違法吸金 OR 銀行法 OR 組織犯罪) (判決 OR 起訴 OR 判刑 OR 法院)'},
            {"label": "📋 法規・修法",
             "news_zh": '(證券交易法 OR 洗錢防制法 OR 銀行法 OR 組織犯罪防制條例) (修正 OR 三讀 OR 草案)'},
            {"label": "🇺🇸 美國執法 DOJ／CFTC",
             "rss": [DOJ, CFTC]},
        ],
    },
    {
        "id": "tw-ip",
        "name": "台灣智財：著作權／商標／專利",
        "desc": "三大領域各自蒐集（判決・侵權・修法）",
        "area": "台灣",
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
        "name": "AI 智財權：著作權／商標／專利",
        "desc": "生成式 AI 對三大智財領域的衝擊（國際＋台灣）",
        "area": "國際",
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
            {"label": "📚 學術論文",
             "scholar": 'music copyright royalties NFT intellectual property finance'},
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
        "area": "國際",
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
