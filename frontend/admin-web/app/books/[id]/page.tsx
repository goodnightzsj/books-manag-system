"use client";
import {
  CloudDownloadOutlined,
  FileImageOutlined,
  ReloadOutlined,
  SaveOutlined,
} from "@ant-design/icons";
import {
  Avatar,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Skeleton,
  Space,
  Typography,
  message,
} from "antd";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

const HASH_TAG: Record<string, string> = {
  done: "tag-ok",
  pending: "tag-warn",
  failed: "tag-danger",
  skipped: "tag-quiet",
};

const HASH_LABEL: Record<string, string> = {
  done: "已校验",
  pending: "待计算",
  failed: "失败",
  skipped: "跳过",
};

export default function BookDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const [book, setBook] = useState<any>(null);
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedCats, setSelectedCats] = useState<string[]>([]);
  const [initialCats, setInitialCats] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const [b, allCats] = await Promise.all([api.getBook(id), api.listCategories()]);
    setBook(b);
    setCategories(allCats as any[]);
    form.setFieldsValue({
      title: b.title,
      subtitle: b.subtitle ?? "",
      author: b.author ?? "",
      publisher: b.publisher ?? "",
      isbn: b.isbn ?? "",
      language: b.language ?? "zh",
      page_count: b.page_count ?? undefined,
      rating: b.rating ?? undefined,
      rating_count: b.rating_count ?? undefined,
      description: b.description ?? "",
      cover_url: b.cover_url ?? "",
      tags: b.tags ?? [],
    });

    // Derive current category associations by scanning each category's books
    // for the current book id. Backend has no "book.categories" endpoint yet;
    // this is the minimum viable call without extra API surface.
    const marked: string[] = [];
    await Promise.all(
      (allCats as any[]).map(async (c) => {
        try {
          const r = await api.listCategoryBooks(c.id, 1, 100);
          if (r.items.some((bb: any) => bb.id === id)) marked.push(c.id);
        } catch {
          /* ignore */
        }
      }),
    );
    setInitialCats(marked);
    setSelectedCats(marked);
  }, [id, form]);

  useEffect(() => {
    load();
  }, [load]);

  async function onSave() {
    setSaving(true);
    try {
      const values = await form.validateFields();
      if (Array.isArray(values.tags) && typeof values.tags[0] === "string") {
        // tags already string[]
      }
      await api.updateBook(id, values);

      // sync category associations
      const toAdd = selectedCats.filter((c) => !initialCats.includes(c));
      const toRemove = initialCats.filter((c) => !selectedCats.includes(c));
      await Promise.all([
        ...toAdd.map((c) => api.addBookToCategory(c, id)),
        ...toRemove.map((c) => api.removeBookFromCategory(c, id)),
      ]);
      message.success("已保存");
      load();
    } catch (e) {
      if ((e as any)?.errorFields) return;
      message.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function resyncMetadata() {
    try {
      await api.queueMetadata(id, true);
      message.success("已入队:元数据重同步");
    } catch (e) {
      message.error((e as Error).message);
    }
  }
  async function resyncCover(remote: boolean) {
    try {
      await api.queueCover(id, remote);
      message.success(remote ? "已入队:远程下载封面" : "已入队:本地提取封面");
    } catch (e) {
      message.error((e as Error).message);
    }
  }

  if (!book)
    return (
      <AppShell>
        <Row gutter={16}>
          <Col xs={24} md={16}>
            <Card bordered={false}>
              <Skeleton active paragraph={{ rows: 6 }} />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card bordered={false} style={{ marginBottom: 16 }}>
              <div style={{ textAlign: "center", padding: "8px 0 16px" }}>
                <Skeleton.Image active style={{ width: 200, height: 280 }} />
              </div>
              <Skeleton active paragraph={{ rows: 3 }} title={false} />
            </Card>
          </Col>
        </Row>
      </AppShell>
    );

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1 style={{ fontFamily: "var(--font-serif)" }}>{book.title}</h1>
          <div
            className="subtitle"
            style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}
          >
            <span>{book.author ?? "—"}</span>
            <span aria-hidden style={{ color: "var(--rule)" }}>
              ·
            </span>
            <span className="ant-tag tag-quiet">
              {String(book.file_format).toUpperCase()}
            </span>
            <span className={`ant-tag ${HASH_TAG[book.hash_status] ?? "tag-quiet"}`}>
              {HASH_LABEL[book.hash_status] ?? book.hash_status}
            </span>
          </div>
        </div>
        <Space>
          <Button onClick={() => router.back()}>返回</Button>
          <Button icon={<ReloadOutlined />} onClick={resyncMetadata}>
            重同步元数据
          </Button>
          <Button icon={<FileImageOutlined />} onClick={() => resyncCover(false)}>
            本地封面
          </Button>
          <Button icon={<CloudDownloadOutlined />} onClick={() => resyncCover(true)}>
            远程封面
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={onSave}
          >
            保存
          </Button>
        </Space>
      </div>

      <Row gutter={16}>
        <Col xs={24} md={16}>
          <Card bordered={false} title="基本信息">
            <Form layout="vertical" form={form} requiredMark={false}>
              <Row gutter={16}>
                <Col span={16}>
                  <Form.Item
                    name="title"
                    label="书名"
                    rules={[{ required: true, message: "书名不能为空" }]}
                  >
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="language" label="语言">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="subtitle" label="副标题">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="author" label="作者">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="publisher" label="出版社">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="isbn" label="ISBN">
                    <Input style={{ fontFamily: "var(--font-mono)" }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="page_count" label="页数">
                    <InputNumber
                      min={0}
                      className="numeric"
                      style={{ width: "100%" }}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="rating" label="评分">
                    <InputNumber
                      min={0}
                      max={10}
                      step={0.1}
                      className="numeric"
                      style={{ width: "100%" }}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="rating_count" label="评分人数">
                    <InputNumber
                      min={0}
                      className="numeric"
                      style={{ width: "100%" }}
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item name="cover_url" label="封面 URL">
                    <Input
                      placeholder="https://..."
                      style={{ fontFamily: "var(--font-mono)" }}
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item name="tags" label="标签">
                    <Select
                      mode="tags"
                      tokenSeparators={[","]}
                      placeholder="输入后回车添加"
                    />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item name="description" label="简介">
                    <Input.TextArea
                      rows={6}
                      style={{ fontFamily: "var(--font-serif)", lineHeight: 1.7 }}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false} title="封面 & 文件" style={{ marginBottom: 16 }}>
            <div style={{ textAlign: "center" }}>
              {book.cover_url ? (
                <Avatar
                  shape="square"
                  src={book.cover_url}
                  style={{
                    width: 200,
                    height: 280,
                    borderRadius: 4,
                    border: "1px solid var(--rule)",
                  }}
                />
              ) : (
                <div
                  style={{
                    width: 200,
                    height: 280,
                    margin: "0 auto",
                    background: "var(--paper-cool)",
                    border: "1px solid var(--rule)",
                    borderRadius: 4,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--ink)",
                    fontFamily: "var(--font-serif)",
                    fontWeight: 600,
                    fontSize: 56,
                    position: "relative",
                  }}
                >
                  <span style={{ position: "relative", zIndex: 1 }}>
                    {book.title?.slice(0, 1) ?? "?"}
                  </span>
                  {/* deboss-style hairline frame */}
                  <span
                    aria-hidden
                    style={{
                      position: "absolute",
                      inset: 8,
                      border: "1px solid var(--rule)",
                      borderRadius: 2,
                    }}
                  />
                </div>
              )}
            </div>
            <Divider style={{ margin: "16px 0" }} />
            <Descriptions
              column={1}
              size="small"
              labelStyle={{ color: "var(--ink-faint)" }}
            >
              <Descriptions.Item label="大小">
                <span className="numeric">
                  {book.file_size
                    ? `${(book.file_size / 1024 / 1024).toFixed(2)} MB`
                    : "—"}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="Hash">
                <Typography.Text
                  copyable
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                    color: "var(--ink)",
                  }}
                >
                  {book.content_hash?.slice(0, 16) ?? "—"}…
                </Typography.Text>
              </Descriptions.Item>
              <Descriptions.Item label="元数据来源">
                <span style={{ color: "var(--ink-soft)" }}>
                  {book.source_provider ?? "—"}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="同步于">
                <span className="numeric" style={{ color: "var(--ink-soft)" }}>
                  {book.metadata_synced_at?.replace("T", " ").slice(0, 19) ?? "—"}
                </span>
              </Descriptions.Item>
            </Descriptions>
          </Card>
          <Card bordered={false} title="分类关联">
            <Select
              mode="multiple"
              style={{ width: "100%" }}
              placeholder="选择分类"
              value={selectedCats}
              onChange={setSelectedCats}
              options={categories.map((c: any) => ({
                label: c.name,
                value: c.id,
              }))}
              optionFilterProp="label"
              showSearch
            />
            <Typography.Paragraph
              type="secondary"
              style={{ fontSize: 12, marginTop: 12 }}
            >
              保存时会调用{" "}
              <code style={{ fontFamily: "var(--font-mono)" }}>POST</code> /{" "}
              <code style={{ fontFamily: "var(--font-mono)" }}>
                DELETE /categories/&#123;id&#125;/books/&#123;book_id&#125;
              </code>{" "}
              完成增删。
            </Typography.Paragraph>
          </Card>
        </Col>
      </Row>
    </AppShell>
  );
}
