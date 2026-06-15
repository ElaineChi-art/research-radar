# -*- coding: utf-8 -*-
"""研究雷達 —— 設定檔。改這裡就能調整追蹤主題與關鍵字。

每個主題會從三個來源聚合：
  news_en / news_zh : Google News 查詢字串（英文 / 中文）
  arxiv             : arXiv API 查詢字串（追新論文）
  court             : CourtListener 查詢字串（美國判決）
"""

TOPICS = [
    {
        "id": "music-ip",
        "name": "音樂智財與投資",
        "desc": "音樂 NFT・版稅・數位音樂授權（論文核心）",
        "news_en": '"music NFT" OR "music royalties" OR "music copyright" OR "music IP"',
        "news_zh": '音樂 NFT OR 音樂版權 OR 版稅 OR 數位音樂授權',
        "arxiv": 'all:"music" AND (all:"copyright" OR all:"royalties" OR all:"NFT" OR all:"licensing")',
        "court": '"music" AND "copyright"',
    },
    {
        "id": "blockchain-gov",
        "name": "區塊鏈演算法治理",
        "desc": "DAO・on-chain governance・智能合約治理（論文範圍）",
        "news_en": '"blockchain governance" OR "DAO governance" OR "on-chain governance"',
        "news_zh": '區塊鏈 治理 OR DAO OR 去中心化 治理',
        "arxiv": 'all:"blockchain governance" OR all:"decentralized autonomous organization" OR all:"on-chain governance" OR all:"smart contract"',
        "court": '"decentralized autonomous organization"',
    },
    {
        "id": "ai-ip",
        "name": "AI 智財權",
        "desc": "生成式 AI 著作權・商標・專利・訓練資料侵權",
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
