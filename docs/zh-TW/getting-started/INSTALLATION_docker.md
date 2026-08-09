[**開始使用**](./getting-started.md) > **安裝** > **Docker** _(目前頁面)_

---

# 使用 Docker Compose 安裝 GBabelDocUI

需要 Docker Engine、Compose v2 與 Git。儲存庫內的 Compose 設定包含必要的持久化掛載與安全限制，是受支援的容器部署方式。

## 本機啟動

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Linux 需要先讓容器使用者能夠寫入綁定的資料目錄：

```bash
mkdir -p data
sudo chown -R 10001:10001 data
```

建置並啟動服務：

```bash
docker compose up -d --build
```

開啟 `http://127.0.0.1:7860/login.html`。本機 Compose 預設設定 `GBABELDOCUI_COOKIE_SECURE=false`，因為服務透過回環 HTTP 存取。

## 透過 HTTPS 公開服務

公開服務前先設定 HTTPS 反向代理，並至少使用以下環境變數啟動：

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

只有第一個管理員必須遠端建立時才需要設定初始化權杖。初始化完成後立即移除該變數並重新啟動服務。

不要擴充服務副本，也不要增加多個 Uvicorn worker。一個 `data/` 目錄只能由一個應用程式程序持有，第二個執行個體使用相同目錄時會主動快速失敗。

## 持久化資料

- `./data:/app/data` 儲存帳戶、設定、任務歷史、上傳檔案與輸出檔案。
- `babeldoc-cache` 命名磁碟區儲存 `/cache` 下的模型與字型快取。
- 容器根檔案系統為唯讀，`/tmp` 使用有容量限制的暫存檔案系統。

禁止提交、封裝或公開 `./data`。

## 檢查與停止

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```

除非明確刪除，`docker compose down` 不會刪除 `./data` 或命名快取磁碟區。
