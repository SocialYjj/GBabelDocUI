# pdf2zh-next 运行时来源

本目录仅内置 GBabelDocUI 实际调用的 `pdf2zh-next` 2.9.0 运行时子集，用于规避该版本发行元数据中 BabelDOC 与 PyMuPDF 约束互相冲突的问题。

- 上游项目：PDFMathTranslate-next / PDFMathTranslate-next
- 上游发行版：`pdf2zh-next==2.9.0`
- 上游 wheel：`pdf2zh_next-2.9.0-py3-none-any.whl`
- wheel SHA-256：`4cf72454dbff21c6c35380aed5e3bfe29278f0fdbe87e83942adf89e33b37c68`
- 核验日期：2026-08-09
- 许可证：AGPL-3.0，见本目录 `LICENSE`

本地修改仅包括：

1. 将内部导入路径移动到 `gbabeldocui._vendor.pdf2zh_next`，避免伪装成独立安装的上游发行包。
2. 只保留 Web 服务使用的配置模型、高阶翻译接口、翻译器和异步桥接代码；不内置上游 CLI、Gradio GUI、HTTP API 和资源文件。
3. 依赖由 GBabelDocUI 的 `pyproject.toml` 显式声明并由项目锁文件统一解析。

除上述命名空间和打包边界调整外，保留文件来自经 SHA-256 核验的官方 PyPI wheel。
