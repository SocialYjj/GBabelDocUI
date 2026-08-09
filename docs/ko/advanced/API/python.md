> This locale currently uses the canonical English text to avoid publishing outdated translated instructions.

# Upstream Python API reference

GBabelDocUI does not expose a stable public Python API. The namespace under `gbabeldocui._vendor.pdf2zh_next` is private implementation detail and may change without compatibility guarantees.

For a supported standalone `pdf2zh-next` CLI or Python API, use the official [PDFMathTranslate-next repository](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next) and follow the documentation for the version you install. Do not replace upstream imports with the private GBabelDocUI vendor namespace.
