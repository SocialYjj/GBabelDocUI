# 改进文档翻译

GBabelDocUI 不使用外部 Weblate 项目。文档翻译通过 [SocialYjj/GBabelDocUI](https://github.com/SocialYjj/GBabelDocUI) 的普通 Pull Request 审查。

## 贡献方式

1. 修改对应的 `docs/<locale>/` 文件。
2. 命令、环境变量名、API 路径和文件路径必须与主文档保持一致。
3. 文档示例中不要加入真实账户、API 密钥、Token、PDF、生成结果或 VPS 数据。
4. 提交前执行 `git diff --check`，条件允许时执行 `uv run mkdocs build`。
5. 在 Pull Request 中说明修改的语言和页面。

如果翻译内容与当前 Web UI 行为不一致，应以仓库实现为准，并在 Pull Request 中说明差异。英文和中文页面是部署与行为的参考页面，其他语言页面不能重新引入上游项目的部署说明。