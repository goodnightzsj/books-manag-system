# Books Management System

> 中文图书馆管理系统 · 后端扫描/元数据/封面 · Web 管理后台 · 跨端阅读器（PDF / EPUB / TXT）
> 默认部署目标：<https://books.9962510.xyz>（reader 在 `/`、admin 在 `/admin/`、API 在 `/api/v1/`）

---

## 下载

按平台取对应文件。所有 4 个工作流（Docker / Desktop / Android / iOS）的产物都汇总在这一个 Release 里。

### 桌面（Tauri）

包装的是 `frontend/reader-web`，本地启动 + 多端阅读体验。

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| Windows | `*_x64_en-US.msi` | **推荐**，MSI 安装包 |
| Windows | `*_x64-setup.exe` | NSIS 安装包 |
| macOS Apple Silicon | `*_aarch64.dmg` | M1 / M2 / M3 / M4 |
| macOS Intel | `*_x64.dmg` | Intel 芯片 |
| Linux Debian/Ubuntu | `*_amd64.deb` | `sudo dpkg -i` |
| Linux 通用 | `*_amd64.AppImage` | `chmod +x && ./...` |

> 未签名版 macOS 首次打开需 右键 → 打开 绕过 Gatekeeper；Windows SmartScreen 弹窗点 "更多信息" → "仍要运行"。

### Android（Capacitor）

| 文件 | 说明 |
| --- | --- |
| `app-release.apk` / `*.aab` | 签名版（需 repo 配置 keystore secrets） |
| `app-debug.apk` | fallback，无 secrets 时自动产出，可侧载测试 |

### iOS（Capacitor）

| 文件 | 说明 |
| --- | --- |
| `*.ipa` | 签名版（需 Apple Developer secrets），通过 Transporter 上传 App Store Connect |
| `App-simulator.app.tar.gz` | fallback，模拟器构建 |

```bash
# 模拟器安装
tar -xzf App-simulator.app.tar.gz
xcrun simctl install booted App.app
xcrun simctl launch booted com.books.reader
```

### Docker（后端 + Admin Web + Reader Web）

按 `v*` tag 同步推送到 Docker Hub，每张镜像都构建 `linux/amd64` 与 `linux/arm64`。具体 tag 列表见 release 附件 `docker-images.txt`。

```bash
# 一键拉取 latest（tag 推送时同步更新）
docker pull <your-dockerhub-user>/books-manag-system-backend:latest
docker pull <your-dockerhub-user>/books-manag-system-admin-web:latest
docker pull <your-dockerhub-user>/books-manag-system-reader-web:latest

# 或固定到具体版本
docker pull <your-dockerhub-user>/books-manag-system-backend:v1.0.0
```

仓库根目录的 `docker-compose.yml` 默认用 `build:`；生产环境可以改成 `image:` 指向上述镜像。

---

## 系统要求

| OS | 最低版本 | 架构 |
| --- | --- | --- |
| Windows | 10+ | x64 |
| macOS | 12 Monterey+ | Intel / Apple Silicon |
| Linux | 现代发行版 | x64 |
| Android | 7.0+ (API 24) | arm64-v8a / armeabi-v7a |
| iOS | 13+ | arm64 |

---

## 安全 / 合规要点

- 后端镜像采用多阶段构建，运行期 **非 root** 用户（`books:1000`），通过 `tini` 进程管理。
- API 提供可开关的速率限制（`RATE_LIMIT_PER_MINUTE`）、`/metrics` Prometheus 指标、JSON 结构化日志（`LOG_JSON=true`）。
- JWT 使用 HS256；密码 bcrypt 存储。
- 镜像不含构建工具（builder 层独立），最小攻击面。

---

## 升级提示

- 第一次升级到带 `book_files` 表（迁移 003）的版本时，启动后会自动 backfill 既有 `books` 行。
- 第一次启用 Meilisearch（设置 `MEILI_URL`）时，可调用一次 `python -c "from app.services.meilisearch_service import MeiliSearchService; ..."` 触发 `reindex_all`，或等待新书入库自动同步。
