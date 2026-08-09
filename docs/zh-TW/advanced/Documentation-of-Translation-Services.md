# 翻譯服務

目前 GBabelDocUI 設定頁提供三種可完整設定的服務。

## OpenAI

請填寫模型與 API 金鑰。Base URL 預設指向公開 OpenAI API，也可改為相容的公用 HTTPS 端點。可選設定包括逾時、溫度、JSON 模式與 reasoning effort。

## Azure OpenAI

請填寫部署名稱、API 金鑰、Azure 資源端點與 API 版本。端點應為資源根網址，而不是完整的 chat-completions 請求 URL。

## Google Gemini

請填寫模型與 API 金鑰；模型支援時可啟用 JSON 模式。

## 認證資訊與端點

- API 金鑰只儲存在伺服器端，不會由設定介面傳回。
- 金鑰留空時會保留原值；只有填入新值才會取代原值。
- 自訂端點會驗證通訊協定、主機、DNS 結果、重新導向與私有網路位址邊界。
- 除非可信部署由管理員明確啟用 `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true`，否則會拒絕私有網路端點。

後端仍保留部分上游翻譯器相容程式碼，但尚未在目前設定介面中提供完整設定的服務，不會顯示在頁面上。
