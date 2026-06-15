# 📡 研究雷達 · 智財 / 區塊鏈 / AI

每天自動聚合三個主題的最新動態，做成一個網頁儀表板，由 GitHub Actions 排程執行、發佈到 GitHub Pages。

主題（改 `config.py` 即可調整）：
1. **音樂智財與投資** — 音樂 NFT、版稅、數位音樂授權
2. **區塊鏈演算法治理** — DAO、on-chain governance、智能合約
3. **AI 智財權** — 生成式 AI 著作權、商標、專利、訓練資料侵權

每個主題彙整三個免費來源：
- 📰 **新聞**（中＋英）：Google News
- 📄 **最新論文**：arXiv（CS / 經濟分類；偏技術方法，法學論文不在 arXiv）
- ⚖️ **美國判決**：CourtListener（依相關度排序）

## 本機執行
```bash
pip install -r requirements.txt
python radar_run.py
# 開 docs/index.html
```

## 上雲（每天自動）
推到 GitHub 後：Settings → Pages 選 `main` 分支 `/docs`；Settings → Actions 給 Read and write 權限。
之後每天 09:00（台灣）自動更新，也可在 Actions 分頁手動 Run workflow。

## 之後可擴充（v2 構想）
- 加台灣資料：司法院裁判書（金融/經濟犯罪判決）、全國法規資料庫法規異動
- 用 embedding 做「類案 / 相似論文」分群與去重
- 法學論文來源（SSRN / Google Scholar，需另解資料取得）
