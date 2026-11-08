# GBabelDocUI 多架构镜像实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 GBabelDocUI 的镜像工作流在 amd64、arm64 原生 runner 上构建并验证；版本发布时合并两个平台的镜像 manifest。

**Architecture:** 保留现有质量检查、发行包检查、Trivy 门禁、SBOM/provenance 和 Cosign 签名。镜像 job 按平台矩阵运行；PR/main 事件只构建扫描，匹配版本 tag 时按 digest 推送，合并任务创建多架构 manifest 并签名。

**Tech Stack:** GitHub Actions、Docker Buildx、GHCR、Trivy、Cosign、Actions artifact。

**Spec:** `.github/workflows/docker-publish.yml` 中现有的 release-tag 校验与单平台镜像 job。

## Global Constraints

- 不读取、修改或删除 `data` 中的真实文件；Docker 构建上下文继续由 `.dockerignore` 排除 `data` 与 `.env`。
- 保留 `pyproject.toml` 版本校验、tag 必须属于 `main` 的规则、SBOM/provenance、Trivy CRITICAL/HIGH 门禁和 Cosign 签名。
- 本次只增加未来版本的多架构发布能力；不更改 `1.2.3`、不重写既有 tag，也不创建新版本 tag。
- `latest` 仅在匹配版本 tag 发布后更新；main/PR 的 arm64 构建用于验证，不向 GHCR 发布。

---

### Task 1：拆分多架构构建与 manifest 发布

**Files:**
- Modify: `.github/workflows/docker-publish.yml`
- Modify: `mkdocs.yml` (exclude the internal plan from the published site)
- Create: `docs/superpowers/plans/2026-11-08-gbabeldocui-arm64-multiarch.md`

**Interfaces:**
- 输入：质量检查结果、package/docs 检查结果、事件版本/tag、Dockerfile。
- 输出：两个平台的构建/扫描结果；匹配版本 tag 时输出带签名的 amd64+arm64 manifest。

- [x] **Step 1：为镜像 job 添加原生 runner 矩阵**

使用 `ubuntu-24.04` 构建 `linux/amd64`，使用 `ubuntu-24.04-arm` 构建 `linux/arm64`。PR/main 构建加载到各自 runner 并扫描；匹配版本 tag 时按 digest 推送，并保留每平台缓存隔离。

- [x] **Step 2：收集合并 digest**

发布构建把每个平台的 digest 上传为 artifact。合并 job 下载 artifact，用 `docker buildx imagetools create` 生成原版本号和 `latest` 标签的多架构 manifest。

- [x] **Step 3：保留安全门禁与签名边界**

每个平台分别运行 Trivy SARIF 报告与 CRITICAL/HIGH 阻断检查；只在版本发布任务中上传 SARIF。合并 manifest 后再用 Cosign 对发布 tag 对应的 manifest 签名。

- [ ] **Step 4：推送 main 并验证两平台构建**

执行完整 GH Actions 工作流，确认 quality、package/docs 与 amd64/arm64 构建及扫描均成功。由于不创建新版本 tag，本阶段不改变当前 GHCR `latest`；发布仍需后续匹配 `pyproject.toml` 的版本 tag。
