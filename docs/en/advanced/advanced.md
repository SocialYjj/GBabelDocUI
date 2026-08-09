# Web UI settings

This page describes GBabelDocUI. It is not a copy of the upstream `pdf2zh_next` command-line reference.

## Translation service

The settings page exposes OpenAI, Azure OpenAI, and Google Gemini. Configure the model or deployment name, API key, and provider-specific endpoint fields. Leaving an API-key field empty preserves the existing server-side key.

## Languages and pages

- Source languages: automatic detection, English, Chinese, Japanese, Korean, French, German, Spanish, and Russian.
- Target languages: English, Chinese, Japanese, Korean, French, German, Spanish, and Russian.
- Page selection accepts the whole document or validated comma-separated pages and ranges such as `1,3,5-8`.

## PDF output

You can create translation-only and bilingual PDFs, choose translated-first or alternating-page layout, restrict output to translated pages, and select the watermark mode. At least one PDF output must remain enabled.

## Advanced translation and PDF behavior

The Web UI supports a custom system prompt, minimum text length, primary font family, terminology extraction, an optional document-layout endpoint, compatibility options, OCR workarounds, table translation, short-line splitting, formula patterns, and selected BabelDOC thresholds.

Custom endpoints are validated by the server. Public HTTPS endpoints are accepted by default; private or loopback destinations require the administrator to set `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` for a trusted deployment.

## Rate limits

- RPM mode: 60–1200 requests per minute and 1–64 concurrent threads.
- Custom mode: QPS 1–20 and 0–64 workers.
- Terminology extraction has a separate service and rate-limit section.

The server validates these limits again and applies per-user and global active-task caps. Do not use client-side changes to bypass server limits.

## Saving settings

Settings are stored per user. Each task receives a sanitized snapshot when it starts. Saved API keys are never returned to the browser or persisted in task history.
