# 改善文件翻譯

GBabelDocUI 不使用外部 Weblate 專案。文件翻譯會透過 [SocialYjj/GBabelDocUI](https://github.com/SocialYjj/GBabelDocUI) 的一般 Pull Request 進行審查。

## 貢獻方式

1. 修改 `docs/<locale>/` 下的對應檔案。
2. 命令、環境變數名稱、API 路徑與檔案路徑必須和基準文件一致。
3. 文件範例中不得加入真實帳戶、API 金鑰、權杖、PDF、產生的輸出或 VPS 資料。
4. 建立 Pull Request 前執行 `git diff --check`；可行時也請執行 `uv run mkdocs build`。
5. 在 Pull Request 中說明修改的語言與頁面。

若翻譯內容與目前 Web UI 行為衝突，應以儲存庫實作為準，並在 Pull Request 中說明差異。英文與中文頁面是部署及行為的參考文件；其他語言頁面不得重新加入上游專案的操作說明。
