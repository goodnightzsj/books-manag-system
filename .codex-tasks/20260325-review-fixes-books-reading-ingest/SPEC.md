# SPEC

## 任务
顺序修复本轮代码审查结论中的 3 个问题：图书创建/更新唯一约束冲突处理、阅读进度 API 去除 legacy notes/bookmarks 写入、duplicate merge 字段列表可维护性优化。

## 形态
single-full

## 范围
- `backend/app/api/books.py`
- `backend/app/services/reading_service.py`
- `backend/app/schemas/reading.py`
- `backend/app/services/book_ingest_service.py`

## 非范围
- 不扩展到其他审查建议
- 不新增测试框架或大规模重构
- 不改动其他 batch 逻辑

## 完成标准
1. 创建/更新图书遇到唯一约束冲突时返回可控 HTTP 错误而不是裸 DB 异常。
2. 阅读进度 API 请求模型与 service 不再写入 legacy `notes` / `bookmarks`。
3. duplicate merge 的字段列表收口为更集中、可维护的常量或统一定义。
4. 相关文件通过最小 `py_compile` 验证。
