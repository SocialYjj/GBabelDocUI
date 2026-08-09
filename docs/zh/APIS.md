# 内部 HTTP API

GBabelDocUI 当前不提供稳定的外部 HTTP API 契约。`/api/` 下的路由是内置 Web UI 使用的认证接口，可能随前端一起变化。

认证使用 `HttpOnly` 会话 Cookie 和 CSRF Cookie/Header，不支持 Bearer Token 或浏览器 `localStorage` 会话。不要绕过 Web UI 边界，也不要在缺少同等认证、CSRF、请求体和来源限制时单独公开内部路由。
