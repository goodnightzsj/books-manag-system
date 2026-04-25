"use client";
import { DeleteOutlined, EditOutlined, SearchOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Input,
  Popconfirm,
  Space,
  Table,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Book = {
  id: string;
  title: string;
  author?: string | null;
  file_format: string;
  hash_status: string;
  rating?: number | null;
  rating_count?: number | null;
  updated_at: string;
};

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

function EmptyBooks({ q }: { q: string }) {
  return (
    <div className="empty-state">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
        <path
          d="M5 4.5h9.5a3 3 0 013 3v12a.5.5 0 01-.78.42L13.6 17.5a1 1 0 00-1.1 0L8.4 19.92a.5.5 0 01-.78-.42v-12a3 3 0 013-3z"
          stroke="currentColor"
          strokeWidth="1.25"
        />
      </svg>
      <div className="label">{q ? `没有匹配「${q}」的书` : "书库为空"}</div>
      <div className="hint">
        {q
          ? "试试更短的关键字，或者切换到 ISBN / 作者维度。"
          : "前往「扫描」页面，添加目录开始入库。"}
      </div>
    </div>
  );
}

export default function BooksPage() {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [data, setData] = useState<{ items: Book[]; total: number } | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.listBooks({ page, page_size: pageSize, q });
      setData({ items: r.items as Book[], total: r.total });
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, q]);

  useEffect(() => {
    load();
  }, [load]);

  async function onDelete(id: string) {
    try {
      await api.deleteBook(id);
      message.success("已删除");
      load();
    } catch (e) {
      message.error((e as Error).message);
    }
  }

  const columns: ColumnsType<Book> = [
    {
      title: "书名",
      dataIndex: "title",
      ellipsis: true,
      render: (title: string, row) => (
        <Link href={`/books/${row.id}`} style={{ color: "var(--ink)" }}>
          <Typography.Text
            strong
            style={{ fontFamily: "var(--font-serif)", fontSize: 15 }}
          >
            {title}
          </Typography.Text>
        </Link>
      ),
    },
    {
      title: "作者",
      dataIndex: "author",
      width: 180,
      ellipsis: true,
      render: (a) => (
        <span style={{ color: "var(--ink-soft)" }}>{a || "—"}</span>
      ),
    },
    {
      title: "格式",
      dataIndex: "file_format",
      width: 90,
      render: (f: string) => (
        <span className="ant-tag tag-quiet">{f?.toUpperCase()}</span>
      ),
    },
    {
      title: "Hash",
      dataIndex: "hash_status",
      width: 110,
      render: (s: string) => (
        <span className={`ant-tag ${HASH_TAG[s] ?? "tag-quiet"}`}>
          {HASH_LABEL[s] ?? s}
        </span>
      ),
    },
    {
      title: "评分",
      dataIndex: "rating",
      width: 110,
      render: (r: number | null, row) =>
        r != null ? (
          <span className="numeric" style={{ color: "var(--ink)" }}>
            <span style={{ color: "var(--accent)" }}>★</span> {r.toFixed(1)}
            <span style={{ color: "var(--ink-faint)", fontSize: 11, marginLeft: 4 }}>
              ({row.rating_count ?? 0})
            </span>
          </span>
        ) : (
          <span style={{ color: "var(--ink-faint)" }}>—</span>
        ),
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      width: 170,
      render: (t: string) => (
        <span className="numeric" style={{ color: "var(--ink-soft)", fontSize: 12.5 }}>
          {t ? t.replace("T", " ").slice(0, 19) : "—"}
        </span>
      ),
    },
    {
      title: "操作",
      key: "ops",
      width: 150,
      fixed: "right",
      render: (_: unknown, row) => (
        <Space size="small">
          <Link href={`/books/${row.id}`}>
            <Button size="small" icon={<EditOutlined />}>
              编辑
            </Button>
          </Link>
          <Popconfirm
            title="确认删除该书？"
            description="删除后书签、批注、阅读进度一并移除。"
            okButtonProps={{ danger: true }}
            onConfirm={() => onDelete(row.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>图书管理</h1>
          <div className="subtitle">
            {data ? (
              <>
                共 <span className="numeric">{data.total}</span> 本
              </>
            ) : (
              "加载中..."
            )}
          </div>
        </div>
        <Input.Search
          placeholder="按书名 / 作者 / ISBN 搜索"
          prefix={<SearchOutlined style={{ color: "var(--ink-faint)" }} />}
          allowClear
          enterButton
          size="large"
          style={{ maxWidth: 420 }}
          onSearch={(v) => {
            setQ(v);
            setPage(1);
          }}
        />
      </div>
      <Card bordered={false}>
        <Table<Book>
          rowKey="id"
          loading={loading}
          dataSource={data?.items ?? []}
          columns={columns}
          size="middle"
          scroll={{ x: 960 }}
          locale={{ emptyText: <EmptyBooks q={q} /> }}
          pagination={{
            current: page,
            pageSize,
            total: data?.total ?? 0,
            showSizeChanger: true,
            pageSizeOptions: [10, 20, 50, 100],
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
        />
      </Card>
    </AppShell>
  );
}
