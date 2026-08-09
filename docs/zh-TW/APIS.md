# 內部 HTTP API

GBabelDocUI 目前不提供穩定的外部 HTTP API 契約。`/api/` 下的路由是內建 Web UI 使用的身分驗證介面，可能隨前端同步變更。

身分驗證採用 `HttpOnly` 工作階段 Cookie，以及 CSRF Cookie/Header 配對；不支援 Bearer Token 或瀏覽器 `localStorage` 工作階段。請勿繞過 Web UI 邊界，也不要在缺少同等身分驗證、CSRF、請求本文與來源限制時，單獨公開內部路由。
