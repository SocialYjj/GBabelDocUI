# GBabelDocUI 多架构镜像实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 GBabelDocUI 的镜像工作流在 amd64、arm64 原生 runner 上构建并验证；版本发布时合并两个平台的镜像 manifest。

**Architecture:** 保留现有质量检查、发行包检查、Trivy 门禁、SBOM/provenance 和 Cosign 签名。镜像 job 按平台矩阵运行；PR/main 事件只构建扫描，匹配版本 tag 时按 digest 推送，合并任务创建多架构 manifest 并签名。

**Tech Stack:** GitHub Actions、Docker Buildx、GHCR、Trivy、Cosign、Actions artifact。

**Spec:** `.github/workflows/docker-publish.yml` 中现有的 release-tag 校验与单平台镜像 job。

## Global Constraints

- 不读取、修改或删除 `data` 中的真实文件；Docker 构建上下文继续由 `.dockerignore` 排除 `data` 与 `.env`。
- 保留 `pyproject.toml` 版本校验、tag 必须属于 `main` 的规则、SBOM/provenance、Trivy CRITICAL/HIGH 门禁和 Cosign 签名。
- 为按用户要求立即更新 `latest`，创建新的补丁版本 `v1.2.4`；保留 `v1.2.3`，不重写既有 tag。
- `latest` 仅在匹配版本 tag 发布后更新；main/PR 的 arm64 构建用于验证，不向 GHCR 发布。

## 执行裁定

- **Ruling:** 用户明确要求 `latest` 立即包含 ARM64，故本次覆盖原计划“不创建新 tag”的限制，发布新补丁版本 `v1.2.4`；不重写 `v1.2.3`。若判断错误，影响是 GHCR 多发布一个补丁版本。

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

推送 main 后等待完整 GH Actions 工作流通过，确认 quality、package/docs 与 amd64/arm64 构建及扫描均成功；随后为同一提交创建并推送匹配项目版本的 `v1.2.4` tag，由发布工作流合并双架构 manifest、签名并更新 GHCR `latest`。不部署 VPS。

## 实施状态（2026-11-08）

- 当前阶段：`bitstring` wheel 安装兼容问题已修复；首次 main 工作流的测试、发行包和标准 pip 安装通过，但 amd64/arm64 Trivy 门禁发现需更新的高危依赖及基础镜像 OpenSSL。
- 已完成内容：项目版本为 `1.2.4`；`bitstring>=4.3.0,<5.0` 已加入运行依赖并通过标准 pip 安装验证。
- 当前修复：应用依赖已升级；Trivy 确认旧版 urllib3/msgpack 来自 Python 基础镜像全局 pip 的 vendored 包。运行镜像不需要 pip/ensurepip，已从 runtime 层移除，并将 BuildKit 缓存按 `uv.lock` 哈希隔离；保留 CRITICAL/HIGH 门禁。
- 兼容性决策：已修复版本的 Pillow 13 和 filelock 4 要求 Python 3.11 及以上；保留项目 Python 3.10 支持，用环境标记让 3.10 使用其兼容版本。容器运行 Python 3.13，将使用已修复版本。
- 后续步骤：完成本地检查后再次推送 main 并等待完整工作流通过，再推送 `v1.2.4`，验证 `latest` manifest 同时含 amd64、arm64。
