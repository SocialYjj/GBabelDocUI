# 參與 GBabelDocUI 開發

GBabelDocUI 是多使用者 Web UI，內建經過校驗的 `pdf2zh-next 2.9.0` 執行時子集。歡迎改善身分驗證、使用者隔離、任務處理、翻譯設定、PDF 輸出、文件與部署。

## 建立 Pull Request 前

1. 閱讀 [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)，並完整保留上游授權與著作權聲明。
2. 不要加入 `data/`、`.env` 檔案、API 金鑰、資料庫、上傳的 PDF、產生的輸出或本機快取。
3. 維持單一程序執行模型：不要加入共用同一個 `data/` 目錄的多個 worker 或副本。
4. 若要進行重大行為或相依套件變更，請先建立 Issue，並說明移轉或操作影響。

## 開發與驗證

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
node --check gbabeldocui/static/js/api.js
node --check gbabeldocui/static/js/auth.js
node --check gbabeldocui/static/js/i18n.js
docker compose config --quiet
```

請使用功能分支，並在 Pull Request 中說明使用者可見行為、資料保留影響與已執行的驗證。行為或部署說明變更時，請同步更新英文與中文文件；其他語言頁面可在對應翻譯完成後更新。

## 文件翻譯

文件翻譯直接在此儲存庫維護。請修改 `docs/<locale>/` 下的對應檔案，並透過一般 Pull Request 提交。GBabelDocUI 沒有外部 Weblate 專案。

## 授權

提交貢獻即表示您同意依本儲存庫的 [AGPL-3.0 授權](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)散布該貢獻。
