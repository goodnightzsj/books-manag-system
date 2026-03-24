# Books Platform Roadmap v2

## 1. 最终技术选型定稿

### 1.1 总体原则
- 保留现有 `backend/` Python 技术栈，不做推倒重来。
- 采用 **Web-first 全端方案**：先把 Web 跑通，再封装 Android / iOS / Windows / macOS。
- PostgreSQL 永远是主数据源；搜索引擎只是投影。
- 重任务全部下沉到 worker，不继续放在 API 请求线程。

### 1.2 最终选型清单

| 领域 | 最终选择 | 说明 |
|---|---|---|
| Backend API | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic | 延续现有基础，风险最低 |
| 主数据库 | PostgreSQL 16 | 主数据、事务、关系、JSON、FTS |
| 缓存 / Broker | Redis 7 | Celery broker、缓存、短锁 |
| 异步任务 | Celery + Celery Beat | 扫描、hash、元数据、封面、索引 |
| 搜索（MVP） | PostgreSQL `pg_trgm` + `tsvector` | 先以最小成本提升搜索 |
| 搜索（Phase 2） | Meilisearch | 用于书目搜索、联想、容错、facets |
| 阅读器 Web | Next.js + React + TypeScript | 多端复用核心代码 |
| Admin Web | Next.js + TypeScript + Ant Design Pro | 后台页面产出速度最快 |
| PDF 阅读 | PDF.js | Web 方案最成熟 |
| EPUB 阅读 | epub.js | 先满足主流电子书阅读 |
| TXT 阅读 | 自研组件 | 实现最简单 |
| 移动端 | Capacitor | 复用 reader-web |
| 桌面端 | Tauri 2 | 复用 reader-web，桌面包更轻 |
| 反向代理 | Nginx | 下载、静态资源、Range 支持 |
| 部署主路径 | Docker Compose | Docker / VPS / Ubuntu / CentOS 统一主路径 |
| 部署回退路径 | systemd + Nginx + `.env` | 适配裸机 / VPS |

### 1.3 为什么最终不选 React Native 全家桶
- 你的难点不是“移动端原生 UI”，而是“多格式阅读 + 多端同步 + 快速交付”。
- Web-first 更适合小团队，同时覆盖后台和阅读器。
- Windows/macOS 用 Tauri 比 RN Windows/macOS 更轻、更容易落地。
- 当前项目还是后端雏形阶段，先把协议、数据模型、任务系统打稳更重要。

### 1.4 搜索定稿
**最终决策**：
- **MVP**：PostgreSQL FTS
- **Phase 2**：Meilisearch
- **暂不进入 OpenSearch/Elasticsearch**

**理由**：
- 你当前最需要的是“书名 / 作者 / ISBN / 分类 / 标签”检索变快。
- Meilisearch 对小团队更友好，部署轻、上手快、体验好。
- 如果未来明确要求“书内正文中文全文检索 + 高亮 + 复杂排序”，再评估 OpenSearch。

### 1.5 数据模型定稿

#### 核心表
1. `books`
   - 书目主实体
   - 包含 title / author / isbn / publisher / description / cover 等元数据

2. `book_files`
   - 一个书目可对应多个文件副本
   - 字段建议：
     - `id`
     - `book_id`
     - `file_path`
     - `file_format`
     - `file_size`
     - `content_hash`
     - `hash_algorithm`
     - `hash_status`
     - `mtime`
     - `is_primary`
     - `indexed_at`

3. `scan_jobs`
   - 目录扫描任务
   - 字段建议：
     - `id`
     - `type`
     - `status`
     - `root_path`
     - `total_items`
     - `processed_items`
     - `success_items`
     - `failed_items`
     - `started_at`
     - `finished_at`
     - `created_by`

4. `scan_job_items`
   - 任务明细 / 错误记录

5. `reading_progress`
   - 每用户、每书一本记录
   - 必须加唯一约束 `(user_id, book_id)`

6. `bookmarks`
   - 独立存书签
   - 不再塞 JSON

7. `annotations`
   - 独立存高亮 / 批注

### 1.6 阅读定位协议定稿
统一 `locator` JSON：
- PDF：`{"type":"pdf_page","page":12,"offset":0.35}`
- EPUB：`{"type":"epub_cfi","cfi":"epubcfi(...)"}`
- TXT：`{"type":"text_offset","start":1234,"end":1301}`

### 1.7 代码仓布局定稿

```text
backend/
frontend/
  admin-web/
  reader-web/
apps/
  desktop-shell/
  mobile-shell/
infra/
  docker/
  deploy/
```

---

## 2. MVP 可执行任务拆解

### Milestone 0：项目基线整理
**目标**：让后续开发不被目录结构和启动方式拖累。

#### Task 0.1
- 新建目录结构：`frontend/admin-web`、`frontend/reader-web`、`apps/desktop-shell`、`apps/mobile-shell`、`infra/`
- 产物：基础 monorepo 目录

#### Task 0.2
- 增加顶层环境变量约定文档
- 输出 `.env.example`
- 明确：DB / Redis / Books Dir / Upload Dir / Search 开关

#### Task 0.3
- 整理 Docker Compose 主路径
- 至少包含：api / worker / redis / postgres / nginx

**验收**
- 一条命令能本地跑通基础服务

---

### Milestone 1：数据库与模型升级
**目标**：把后续功能依赖的表结构先打好。

#### Task 1.1
- 设计 `book_files` 表
- 让 `books` 与文件副本解耦

#### Task 1.2
- 设计 `scan_jobs`、`scan_job_items`

#### Task 1.3
- 给 `reading_progress` 增加唯一约束 `(user_id, book_id)`

#### Task 1.4
- 新增 `bookmarks`、`annotations`
- `ReadingProgress.notes` / `bookmarks` 后续逐步废弃

#### Task 1.5
- 编写 Alembic 迁移

**验收**
- 数据迁移可执行
- 老数据可兼容迁移

---

### Milestone 2：扫描任务系统化
**目标**：替换当前 `BackgroundTasks` 模式。

#### Task 2.1
- 引入 Celery / Redis
- 建立 worker 进程启动方式

#### Task 2.2
- `POST /scanner/scan-directory` 改为创建 job
- 返回 `job_id`

#### Task 2.3
- worker 执行目录扫描
- 更新 `scan_jobs.processed_items`

#### Task 2.4
- 增加查询任务状态 API
- `GET /scanner/jobs/{job_id}`
- `GET /scanner/jobs`

#### Task 2.5
- 增加失败项记录与重试能力

**验收**
- 扫描目录后能实时看到任务进度和失败信息

---

### Milestone 3：文件 hash 与去重
**目标**：从路径判重升级为内容判重。

#### Task 3.1
- 给扫描流程加入 quick fingerprint
- 基于 size + mtime + chunk 做首轮判断

#### Task 3.2
- worker 异步补全 `sha256` 内容 hash

#### Task 3.3
- 去重规则改为：
  - `content_hash` 优先
  - `file_path` 只代表副本位置

#### Task 3.4
- 增加 hash 状态字段：pending / done / failed

**验收**
- 同一本书换路径不会重复入库
- 哈希失败可重试

---

### Milestone 4：搜索升级
**目标**：把当前 `ILIKE` 搜索提升为可用版本。

#### Task 4.1
- 在 PostgreSQL 上启用 `pg_trgm`

#### Task 4.2
- 为 `title` / `author` / `isbn` / `publisher` / 分类建立索引策略

#### Task 4.3
- 把 `GET /books` 搜索改为 FTS + trigram

#### Task 4.4
- 支持排序与分页稳定化

**验收**
- 搜索明显快于当前实现
- 支持模糊搜索和分页

---

### Milestone 5：阅读进度与基础同步 API
**目标**：先完成“阅读进度同步”，笔记下一阶段再扩展。

#### Task 5.1
- 增加 Pydantic schemas：
  - `ReadingProgressCreate`
  - `ReadingProgressUpdate`
  - `ReadingProgressResponse`

#### Task 5.2
- 增加 API：
  - `GET /reading-progress/{book_id}`
  - `PUT /reading-progress/{book_id}`
  - `GET /reading-progress/recent`

#### Task 5.3
- 落实统一 locator 字段

**验收**
- Web 端能保存并恢复阅读位置

---

### Milestone 6：文件服务与下载优化
**目标**：让下载和阅读流更稳。

#### Task 6.1
- 补 Range 请求支持

#### Task 6.2
- 优化 MIME / 缓存头 / 文件响应

#### Task 6.3
- 抽离文件访问层，为后续 MinIO/S3 留接口

**验收**
- PDF 大文件可稳定流式阅读
- 下载链接可正常工作

---

### Milestone 7：Admin Web（MVP）
**目标**：先把后台管理做出来。

#### Task 7.1
- 初始化 `frontend/admin-web`
- Next.js + Ant Design Pro

#### Task 7.2
- 接入登录鉴权

#### Task 7.3
- 图书列表 / 图书详情 / 图书编辑

#### Task 7.4
- 扫描任务页
- 任务状态、进度、失败项

#### Task 7.5
- 分类管理页

#### Task 7.6
- 元数据手动同步 / 封面提取操作

**验收**
- 管理员可通过后台完成主要管理动作

---

### Milestone 8：Reader Web（MVP）
**目标**：先支持主流阅读能力。

#### Task 8.1
- 初始化 `frontend/reader-web`
- Next.js + React + TypeScript

#### Task 8.2
- 登录 / 书库页 / 搜索页 / 详情页

#### Task 8.3
- 接入 PDF.js

#### Task 8.4
- 接入 epub.js

#### Task 8.5
- 实现 TXT 阅读器

#### Task 8.6
- 与阅读进度 API 联动

**验收**
- Web 可阅读 PDF / EPUB / TXT
- 刷新后能恢复阅读进度

---

### Milestone 9：部署交付
**目标**：让 Docker / VPS / Ubuntu / CentOS 都能部署。

#### Task 9.1
- 编写 `docker-compose.yml`

#### Task 9.2
- 修正 `entrypoint.sh` 硬编码主机名问题

#### Task 9.3
- 提供 `infra/deploy/systemd/` 模板

#### Task 9.4
- 提供部署文档：
  - Docker
  - Ubuntu + systemd
  - CentOS + systemd

**验收**
- 至少 2 种方式可完成部署

---

## 3. MVP 实施顺序（严格依赖）
1. Milestone 0：项目基线整理
2. Milestone 1：数据库与模型升级
3. Milestone 2：扫描任务系统化
4. Milestone 3：文件 hash 与去重
5. Milestone 4：搜索升级
6. Milestone 5：阅读进度 API
7. Milestone 6：文件服务优化
8. Milestone 7：Admin Web
9. Milestone 8：Reader Web
10. Milestone 9：部署交付

---

## 4. MVP 完成定义
满足以下条件即视为 MVP 完成：
- 能扫描指定目录并异步入库
- 每个文件有 hash 状态，主去重基于内容 hash
- 图书基本 CRUD 正常
- 搜索速度明显优于当前 `ILIKE`
- 管理后台可用
- Web 可阅读 PDF / EPUB / TXT
- 阅读进度可保存和恢复
- Docker / VPS / Ubuntu / CentOS 至少有稳定部署路径

---

## 5. 后续建议
完成 MVP 后，再进入：
- Phase 2：annotations / bookmarks / 多端封装 / Meilisearch
- Phase 3：缓存、任务中心、观测、体验打磨

---

## 6. 参考上下文
- 当前扫描判重：`backend/app/services/scanner_service.py:72-109`
- 当前扫描 API：`backend/app/api/scanner.py:42-234`
- 当前搜索实现：`backend/app/api/books.py:25-32`
- 当前阅读进度模型：`backend/app/models/reading.py:17-37`
- 当前部署硬编码：`backend/entrypoint.sh:9-35`
- 现有历史方案：`architecture.md:34-147`
