# 📋 实施计划：Books 多端阅读与管理平台路线图

## 任务类型
- [ ] 前端 (→ Gemini)
- [ ] 后端 (→ Codex)
- [x] 全栈 (→ 并行)

## 当前基线
- 已有后端能力：认证、图书 CRUD、分类、扫描、文件下载/流式传输、规则推荐。
- 当前扫描仍以 `file_path + file_size` 判重，而非内容哈希：`backend/app/services/scanner_service.py:72-109`
- 当前目录扫描仅用 `BackgroundTasks`，没有任务持久化/进度查询：`backend/app/api/scanner.py:42-56`
- 当前搜索是 `ILIKE` 查询，性能和体验都不够：`backend/app/api/books.py:25-32`
- 当前阅读进度只有 ORM，无 schema / API / 细粒度笔记模型：`backend/app/models/reading.py:17-37`
- 当前部署脚本写死 `postgres` / `redis` 主机名，不利于 VPS / 裸机部署：`backend/entrypoint.sh:11-35`
- 现有架构草案倾向 React Native 全家桶：`architecture.md:98-147`

---

## A. 技术方案建议

### 1) 后端
**建议**：继续使用 Python + FastAPI + SQLAlchemy + Alembic，不做整栈重写。

**推荐版本**
- Python 3.11/3.12
- FastAPI 0.11x
- SQLAlchemy 2.0
- Alembic 最新稳定版

**原因**
- 现有后端已经有可用基础，不值得为规划阶段重写。
- 当前瓶颈不在 sync/async，而在“后台任务、搜索、阅读同步、部署抽象”。
- 大量 I/O 型工作应下沉到 worker，不应继续留在请求线程。

### 2) 搜索
**分层建议**
- **MVP**：PostgreSQL `pg_trgm` + `tsvector`
- **增强期**：根据实际搜索目标二选一：
  - **Meilisearch**：适合书目元数据搜索、联想、容错、快速上线
  - **OpenSearch / Elasticsearch**：适合中文正文级全文搜索、复杂排序、高亮、分析器

**决策建议**
- 如果你要的是“书名/作者/ISBN/标签/分类搜索非常快”，MVP 直接先做 PostgreSQL FTS 即可。
- 如果你要的是“书内正文全文检索 + 中文分词 + 高亮”，增强期直接走 OpenSearch，不建议中间绕远。

### 3) 异步任务
**建议**：Redis + Celery + Celery Beat

**用于**
- 目录扫描
- 文件哈希计算
- 外部元数据抓取
- 封面提取 / 下载
- 内容抽取与索引同步
- 定时重建索引 / 清理失效任务

### 4) 存储
**建议**
- 主数据库：PostgreSQL 15/16
- 缓存/队列：Redis 7
- 文件存储：优先本地磁盘 + 可选对象存储抽象（S3/MinIO 兼容）

**结构建议**
- `books`：书目主记录
- `book_files`：文件副本记录（路径、大小、哈希、格式、状态）
- `scan_jobs` / `scan_job_items`：扫描作业与明细
- `reading_progress`：阅读进度
- `annotations`：高亮/批注
- `bookmarks`：书签
- `sync_devices` / `sync_cursors`（可选）：设备同步游标

### 5) 跨端客户端
**推荐主方案**：**Web-first 单代码库**
- Reader Web：Next.js / React
- Android / iOS：Capacitor 封装 Reader Web
- Windows / macOS：Tauri 2 封装 Reader Web

**阅读内核建议**
- PDF：PDF.js
- EPUB：epub.js 或 Foliate 系阅读引擎
- TXT：自研阅读组件
- MOBI / AZW3：入库时异步转 EPUB/HTML 作为内部阅读格式，保留原始文件供下载

**原因**
- 对小团队来说，这条路线最现实，能最快覆盖 Web + 移动 + 桌面。
- 阅读器最难的是“格式渲染 + 位置同步 + 离线缓存”，不建议同时再承担 RN Windows/macOS 适配成本。

### 6) 后台管理
**建议**：独立 Web Admin
- Next.js 15
- UI：shadcn/ui 或 Ant Design Pro（二选一）
- 数据表格：TanStack Table
- 图表：ECharts / Recharts

**取舍**
- 要更快：Ant Design Pro
- 要更现代、更可定制：shadcn/ui

### 7) 部署
**建议**
- 主路径：Docker Compose
- 回退路径：systemd + `.env` + Nginx（适配 VPS / Ubuntu / CentOS）
- 反向代理：Nginx / Caddy
- 观测：结构化日志 + health endpoint + queue metrics

**部署原则**
- 所有数据库、Redis、搜索、卷路径全部环境变量化
- 不再写死 `postgres` / `redis`
- Linux 服务器是官方部署目标；Windows 服务器不作为优先支持对象

---

## B. 可比较方案（3 选 1）

### 方案 A：最小增量栈
**组成**
- FastAPI + PostgreSQL + Redis + Celery
- 搜索：PostgreSQL FTS
- Admin：Next.js
- 阅读器：先 Web，后续再封装客户端

**优点**
- 改动最小，最快交付
- 运维最轻
- 最适合先把现有项目做成可用产品

**缺点**
- 多端体验不是第一天就齐全
- 搜索体验上限一般
- 阅读器跨端落地会推迟

**适合**
- 先做后台和 Web，后续再扩端

### 方案 B：Web-first 全端方案（推荐）
**组成**
- FastAPI + PostgreSQL + Redis + Celery
- 搜索：MVP PostgreSQL FTS，增强期按需求上 Meilisearch 或 OpenSearch
- Admin：Next.js 独立项目
- Reader：Next.js/React + PDF.js/epub.js
- Android/iOS：Capacitor
- Windows/macOS：Tauri 2

**优点**
- 小团队开发效率最高
- 五端复用度高
- 后台与阅读器都能走成熟 Web 技术栈
- 运维成本仍可控

**缺点**
- 桌面/移动端是封装型，不是完全原生
- 极端大文件阅读体验需要专项优化
- MOBI/AZW3 需要格式归一化策略

**适合**
- 你的当前需求组合：后台 + 阅读器 + 多端 + 快速落地

### 方案 C：React Native 全家桶
**组成**
- FastAPI + PostgreSQL + Redis + Celery
- Admin：独立 Web Admin
- Reader：React Native + React Native Web + RN Windows/macOS

**优点**
- 移动端体验潜力高
- 与现有 `architecture.md` 方向一致
- TypeScript 生态成熟

**缺点**
- 实际不是“真正零成本五端”
- Windows/macOS/Web 会有更多平台差异
- 阅读器库组合更复杂
- 小团队维护成本更高

**适合**
- 团队强 React Native，且愿意接受更长交付周期

---

## C. 推荐方案

### 推荐：**方案 B（Web-first 全端方案）**

### 推荐理由
1. **最符合当前代码基线**：现有后端能保留，重点补齐缺失能力即可。
2. **最适合小团队**：语言收敛为 Python + TypeScript。
3. **最快覆盖五端**：Reader Web 一套代码，Capacitor/Tauri 做平台打包。
4. **后台管理最好做**：Admin 天然更适合浏览器优先。
5. **风险最可控**：遇到某个端的包装问题，不影响 Web 主线。

### 推荐架构图（逻辑）
- `api`：认证、书目、分类、下载、搜索代理、同步 API、管理统计
- `worker`：扫描、哈希、元数据增强、封面、抽取、索引同步
- `postgres`：真相源
- `redis`：broker / cache / lock
- `search`：FTS / Meilisearch / OpenSearch（按阶段引入）
- `admin-web`：后台管理
- `reader-web`：阅读器主应用
- `mobile-shell`：Capacitor
- `desktop-shell`：Tauri

---

## D. 分阶段实施计划（MVP → 增强 → 完善）

## Phase 1：MVP（先把产品主链打通）

### 目标
做出一个能部署、能扫描、能管理、能搜索、能在 Web 端阅读的最小可用系统。

### 后端任务
1. **数据模型补齐**
   - 在 `books` 或新建 `book_files` 中加入：
     - `content_hash`
     - `hash_algorithm`
     - `hash_status`
     - `last_hashed_at`
   - `reading_progress` 增加 `(user_id, book_id)` 唯一约束
   - 新增 `scan_jobs` / `scan_job_items`

2. **扫描链路改造**
   - `POST /scanner/scan-directory` 从 `BackgroundTasks` 改为创建 job
   - worker 执行目录扫描与哈希计算
   - API 可查询 job 进度

3. **搜索升级（先不引入重型搜索）**
   - 将 `books` 搜索从 `ILIKE` 升级为 PostgreSQL FTS + `pg_trgm`
   - 搜索字段覆盖：title / author / isbn / publisher / tags / category

4. **阅读同步基础 API**
   - 增加 `reading_progress` schema + CRUD
   - 支持：进入阅读、更新进度、最近阅读、继续阅读

5. **文件服务补齐**
   - 支持标准 Range 请求
   - 保持下载与流式接口兼容

6. **部署改造**
   - 增加 `docker-compose.yml`
   - 增加 `.env.example`
   - 移除 `entrypoint.sh` 中对 `postgres` / `redis` 的硬编码依赖
   - 增加 systemd 部署文档

### 前端任务
1. 建立 `admin-web`
   - 登录页
   - 图书列表
   - 图书详情
   - 扫描任务页
   - 分类管理页
   - 手动同步元数据/封面

2. 建立 `reader-web`
   - 登录
   - 书库浏览
   - 搜索
   - PDF 阅读
   - EPUB 阅读
   - TXT 阅读
   - 基础阅读进度同步

### 预期产物
- Docker 一键启动
- 可在 Ubuntu/CentOS/VPS 上部署
- 可扫描目录并记录 hash
- 可搜索和下载
- Web 端可阅读与续读

### MVP 伪代码
```text
POST /scanner/scan-directory
  -> create ScanJob(status='queued')
  -> enqueue celery task(scan_job_id)
  -> return job_id

worker(scan_job_id)
  -> walk directory
  -> for each file:
       quick fingerprint
       upsert file record
       compute content hash
       extract local metadata
       fetch external metadata
       persist book/file
       update search projection
  -> mark job progress / errors
```

---

## Phase 2：增强期（补齐多端与笔记能力）

### 目标
让系统从“可用”升级到“多端可持续使用”。

### 后端任务
1. 新增 `annotations` / `bookmarks` 表
2. 设计统一 `locator` 结构
   - PDF: page + offset
   - EPUB: CFI
   - TXT: text offset
3. 增加增量同步接口
   - `sync/pull`
   - `sync/push`
   - 幂等写入、LWW 冲突策略
4. 引入搜索服务
   - 若偏书目搜索：Meilisearch
   - 若偏中文正文全文：OpenSearch
5. 内容抽取
   - PDF/EPUB/TXT 的文本抽取与异步索引
6. 外部元数据 provider 抽象
   - Google Books / Open Library / 豆瓣适配器

### 前端任务
1. `reader-web` 增加笔记/书签/高亮
2. Android / iOS 用 Capacitor 打包
3. Windows / macOS 用 Tauri 打包
4. 加入离线缓存
5. 最近阅读 / 书签跳转 / 主题切换 / 字体设置

### 预期产物
- 五端都能登录、阅读、同步进度
- 笔记和书签跨端可见
- 搜索体验显著提升
- 扫描、同步、索引都可追踪

### 增强期伪代码
```text
saveAnnotation(book_id, locator, content)
  -> validate locator by format
  -> upsert annotation(client_mutation_id)
  -> set updated_at
  -> return sync token

syncPull(device_id, since_token)
  -> return changed progress/bookmarks/annotations
```

---

## Phase 3：完善期（体验、性能、运维）

### 目标
把系统打磨成可长期使用、可维护、可扩展的产品。

### 后端任务
1. 任务中心
   - 失败重试
   - 取消任务
   - 批量重扫
2. 性能优化
   - Redis 缓存 dashboard / 热门搜索 / 推荐结果
   - 下载与封面分层缓存
   - 大文件分块与限流
3. 高级搜索
   - facets / suggestions / typo tolerance / 高亮
4. 推荐系统升级
   - 从规则推荐升级到内容推荐 / 混合推荐
5. 对象存储抽象
   - 本地磁盘 / MinIO / S3 兼容
6. 监控与告警
   - API、任务、索引、失败率、队列积压

### 前端任务
1. 美化后台 UI
2. 阅读器沉浸式模式
3. 高亮颜色、导出笔记、摘录管理
4. Dashboard 统计图和任务中心
5. 多语言/主题支持

### 预期产物
- 适合 1万+ 图书规模
- 后台好看且可运营
- 多端体验稳定
- 具备生产可维护性

---

## E. 需要优先澄清的关键决策

1. **单用户还是多用户？**
   - 如果只是“家庭/个人书库”，很多权限和同步复杂度可降低。
   - 如果是多用户，必须优先设计租户/权限/隔离边界。

2. **搜索目标是书目搜索还是正文全文搜索？**
   - 这会直接决定 PostgreSQL / Meilisearch / OpenSearch 的路线。

3. **MOBI/AZW3 是“下载即可”还是“必须内置阅读”？**
   - 若必须阅读，建议尽早确认“导入即转换”的策略。

4. **离线优先还是在线优先？**
   - 若强离线，客户端同步和冲突解决必须前置设计。

5. **部署目标是自托管为主，还是未来考虑 SaaS？**
   - 自托管优先时，Docker + Compose + systemd 最关键。
   - SaaS 优先时，需要更早设计对象存储、审计、限流、监控。

6. **目标规模是多少？**
   - 1 人 1 万本书，与 1000 用户并发阅读，是两套不同系统。

7. **后台是运营型还是仅管理型？**
   - 若要统计、任务中心、审计日志，需要更早规划聚合表和 event log。

---

## 关键文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/scanner_service.py:30-128` | 修改 | 扫描逻辑从路径判重升级为内容哈希 / 文件记录 |
| `backend/app/api/scanner.py:42-234` | 修改 | 目录扫描改为 job 化，补充 job 查询接口 |
| `backend/app/api/books.py:14-42` | 修改 | 搜索从 `ILIKE` 升级到 FTS / 搜索投影 |
| `backend/app/models/book.py:25-66` | 修改 | 增加 hash / 文件关系 / 索引字段 |
| `backend/app/models/reading.py:17-37` | 修改 | 进度约束与关系完善 |
| `backend/app/schemas/` | 新增/修改 | 补 reading progress / annotations / bookmarks schema |
| `backend/alembic/versions/` | 新增 | 数据库迁移 |
| `backend/entrypoint.sh:9-87` | 修改 | 取消硬编码依赖，支持 VPS / 裸机环境变量 |
| `docker-compose.yml` | 新增 | Compose 部署入口 |
| `frontend/admin-web/` | 新增 | 后台管理前端 |
| `frontend/reader-web/` | 新增 | 阅读器 Web 前端 |
| `desktop-shell/` | 新增 | Tauri 封装 |
| `mobile-shell/` | 新增 | Capacitor 封装 |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 首次全库 hash 很慢 | 采用 quick fingerprint + 后台补全完整 hash |
| 外部 API 不稳定 | provider 抽象 + 重试 + 熔断 + 任务补偿 |
| 阅读位置跨格式不统一 | 统一 locator 协议，按格式存位置信息 |
| 中文全文搜索复杂 | 先分清书目搜索 vs 正文搜索，再选引擎 |
| 多端打包维护成本上升 | 采用 Web-first + Capacitor/Tauri，避免多套原生实现 |
| VPS / 裸机部署差异大 | Compose 主路径 + systemd 回退路径 + 环境变量化 |

---

## SESSION_ID（供后续执行参考）
- CODEX_SESSION: `019d1fcd-c914-7ff1-a3fe-a07b5d1b445f`
- GEMINI_SESSION: `unavailable (gemini capacity exhausted / HTTP 429)`
