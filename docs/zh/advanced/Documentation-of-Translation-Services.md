# 翻译服务

当前 GBabelDocUI 设置页提供三种可完整配置的服务。

## OpenAI

填写模型和 API 密钥。Base URL 默认指向公开 OpenAI API，也可改为兼容的公共 HTTPS 端点。可选设置包括超时、温度、JSON 模式和 reasoning effort。

## Azure OpenAI

填写部署名称、API 密钥、Azure 资源端点和 API 版本。端点应是资源根地址，不是完整的 chat-completions 请求 URL。

## Google Gemini

填写模型和 API 密钥；模型支持时可启用 JSON 模式。

## 凭据和端点

- API 密钥只保存在服务端，不会由设置接口返回。
- 密钥留空会保留原值，填写新值才会替换。
- 自定义端点会校验协议、主机、DNS 结果、重定向和私网地址边界。
- 除非可信部署由管理员显式启用 `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true`，否则拒绝私网端点。

后端仍保留部分上游翻译器兼容代码，但没有完整当前设置界面的服务不会出现在页面中。
