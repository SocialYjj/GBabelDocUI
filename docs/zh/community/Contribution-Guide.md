# 为 GBabelDocUI 做贡献

GBabelDocUI 是基于官方 `pdf2zh-next` 运行时的多用户 Web UI 适配层。欢迎改进认证与用户隔离、任务管理、翻译设置、PDF 输出、文档和部署流程。

## 提交 Pull Request 前

1. 阅读 [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)，保留上游项目的许可证和版权声明。
2. 不要提交 `data/`、`yuan/`、`.env` 文件、API 密钥、数据库、上传的 PDF、生成结果或本地缓存。
3. 保持单进程执行模型；不要让多个 worker 或副本共享同一个 `data/` 目录。
4. 重大行为变化或依赖变更应先提交 Issue，说明迁移方式和运维影响。

## 开发与验证

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

请使用功能分支，并在 Pull Request 中说明用户可见行为、数据保留影响和实际执行的验证。行为或部署说明发生变化时，应同步更新英文和中文文档；其他语言页面在有对应翻译时再更新。

## 文档翻译

文档翻译维护在本仓库中。请修改对应的 `docs/<locale>/` 文件，并像普通代码一样提交 Pull Request。GBabelDocUI 没有外部 Weblate 项目。

## 许可证

提交贡献即表示同意按照本仓库的 [AGPL-3.0 许可证](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE) 发布贡献内容。