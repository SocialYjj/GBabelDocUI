[**开始使用**](./getting-started.md) > **安装** > **Docker** _(当前)_

---

# 使用 Docker Compose 安装 GBabelDocUI

需要 Docker Engine、Compose v2 和 Git。仓库内的 Compose 配置包含必要的持久化挂载和安全限制，是受支持的容器部署方式。

## 本机启动

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Linux 需要先让容器用户能够写入绑定的数据目录：

```bash
mkdir -p data
sudo chown -R 10001:10001 data
```

构建并启动服务：

```bash
docker compose up -d --build
```

打开 `http://127.0.0.1:7860/login.html`。本机 Compose 默认设置 `GBABELDOCUI_COOKIE_SECURE=false`，因为服务通过回环 HTTP 访问。

## 通过 HTTPS 公开服务

公开服务前先配置 HTTPS 反向代理，并至少使用以下环境变量启动：

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

只有首个管理员必须远程创建时才需要设置初始化令牌。初始化完成后立即移除该变量并重启服务。

不要扩容服务，也不要增加多个 Uvicorn worker。一个 `data/` 目录只能由一个应用进程持有，第二个实例使用相同目录时会主动快速失败。

## 持久化数据

- `./data:/app/data` 保存账户、设置、任务历史、上传文件和输出文件。
- `babeldoc-cache` 命名卷保存 `/cache` 下的模型和字体缓存。
- 容器根文件系统只读，`/tmp` 使用有容量限制的临时文件系统。

禁止提交、打包或公开 `./data`。

## 检查和停止

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```

除非显式删除，`docker compose down` 不会删除 `./data` 或命名缓存卷。
