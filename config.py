# -*- coding: utf-8 -*-
"""研究雷達 —— 設定檔。改這裡就能調整追蹤主題與關鍵字。

每個主題會從三個來源聚合：
  news_en / news_zh : Google News 查詢字串（英文 / 中文）
  arxiv             : arXiv API 查詢字串（追新論文）
  court             : CourtListener 查詢字串（美國判決）
"""

TOPICS = [
    # ── 台灣法律（V2，免註冊新聞層；判決全文監測待 v2.1 接司法院 API）──
    {
        "id": "tw-financial-crime",
        "name": "台灣金融／經濟犯罪",
        "desc": "內線交易・背信・掏空・證券詐欺・洗錢（重金庭領域）",
        "kind": "tw",
        "cols": [
            {"label": "⚖️ 判決・訴訟",
             "q": '(內線交易 OR 背信 OR 掏空 OR 證券詐欺 OR 洗錢防制) (判決 OR 起訴 OR 判刑 OR 法院)'},
            {"label": "📋 法規・修法",
             "q": '(證券交易法 OR 洗錢防制法 OR 銀行法 OR 證交法) (修正 OR 三讀 OR 草案 OR 修法)'},
            {"label": "📰 動態・評析",
             "q": '金融犯罪 OR 經濟犯罪 OR 重大經濟犯罪 OR 金融犯罪防制'},
        ],
    },
    {
        "id": "tw-ip",
        "name": "台灣智財（著作權・商標・專利）",
        "desc": "台灣智財判決、修法動態，與 AI×智財",
        "kind": "tw",
        "cols": [
            {"label": "⚖️ 判決・訴訟",
             "q": '(著作權 OR 商標 OR 專利) (判決 OR 侵權 OR 訴訟 OR 智慧財產法院)'},
            {"label": "📋 法規・修法",
             "q": '(著作權法 OR 商標法 OR 專利法) (修正 OR 三讀 OR 草案)'},
            {"label": "📰 AI×智財 動態",
             "q": 'AI 著作權 OR 生成式AI 智財 OR 智慧財產 人工智慧'},
        ],
    },
    # ── 國際研究（V1）──
    {
        "id": "music-ip",
        "name": "音樂智財與投資",
        "desc": "音樂 NFT・版稅・數位音樂授權（論文核心）",
        "kind": "intl",
        "news_en": '"music NFT" OR "music royalties" OR "music copyright" OR "music IP"',
        "news_zh": '音樂 NFT OR 音樂版權 OR 版稅 OR 數位音樂授權',
        "arxiv": 'all:"music" AND (all:"copyright" OR all:"royalties" OR all:"NFT" OR all:"licensing")',
        "court": '"music" AND "copyright"',
    },
    {
        "id": "blockchain-gov",
        "name": "區塊鏈演算法治理",
        "desc": "DAO・on-chain governance・智能合約治理（論文範圍）",
        "kind": "intl",
        "news_en": '"blockchain governance" OR "DAO governance" OR "on-chain governance"',
        "news_zh": '區塊鏈 治理 OR DAO OR 去中心化 治理',
        "arxiv": 'all:"blockchain governance" OR all:"decentralized autonomous organization" OR all:"on-chain governance" OR all:"smart contract"',
        "court": '"decentralized autonomous organization"',
    },
    {
        "id": "ai-ip",
        "name": "AI 智財權",
        "desc": "生成式 AI 著作權・商標・專利・訓練資料侵權",
        "kind": "intl",
        "news_en": '"AI copyright" OR "generative AI" AND (copyright OR patent OR trademark)',
        "news_zh": 'AI 著作權 OR 生成式 AI 著作權 OR AI 專利 OR AI 訓練資料 侵權',
        "arxiv": '(all:"copyright" OR all:"intellectual property" OR all:"patent") AND (all:"generative" OR all:"large language model" OR all:"diffusion")',
        "court": '"artificial intelligence" AND "copyright"',
    },
]

# 每個來源各取幾則
NEWS_EN_LIMIT = 6
NEWS_ZH_LIMIT = 4
ARXIV_LIMIT = 5
COURT_LIMIT = 5
TW_COL_LIMIT = 6   # 台灣主題每欄（中文新聞）取幾則
