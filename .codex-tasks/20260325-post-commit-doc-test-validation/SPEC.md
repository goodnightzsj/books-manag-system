# SPEC

## 任务
提交后的收尾工作：先做本轮 review fixes 的最小 llmdoc 同步，再按顺序推进回归测试、可复现运行闭环、完整 smoke。

## 形态
- single-full

## 范围
- 第 1 步仅更新以下 llmdoc 文件：
  - `llmdoc/reference/api-endpoints.md`
  - `llmdoc/reference/schemas-reference.md`
  - `llmdoc/architecture/services-architecture.md`
- 后续步骤再进入测试与验证，不在本步扩展实现代码。

## 完成标准
1. llmdoc 反映 books create/update 唯一约束冲突返回 409。
2. llmdoc 反映 `ReadingProgressUpdate` 不再接受 legacy `notes` / `bookmarks`。
3. llmdoc 反映 `BookIngestService` duplicate merge 字段集中维护。
4. 本步完成后记录最小验证结果与下一步。