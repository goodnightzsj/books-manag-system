"use client";
import { DeleteOutlined, EditOutlined, SearchOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Input,
  Popconfirm,
  Space,
  Table,
  Tag,
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

const hashColor: Record<string, string> = {
  done: "green",
  pending: "gold",
  failed: "red",
  skipped: "default",
};

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
        <Link href={`/books/${row.id}`}>
          <Typography.Text strong>{title}</Typography.Text>
        </Link>
      ),
    },
    { title: "作者", dataIndex: "author", width: 180, ellipsis: true, render: (a) => a || "—" },
    {
      title: "格式",
      dataIndex: "file_format",
      width: 90,
      render: (f: string) => <Tag color="geekblue">{f?.toUpperCase()}</Tag>,
    },
    {
      title: "Hash",
      dataIndex: "hash_status",
      width: 110,
      render: (s: string) => <Tag color={hashColor[s] ?? "default"}>{s}</Tag>,
    },
    {
      title: "评分",
      dataIndex: "rating",
      width: 110,
      render: (r: number | null, row) =>
        r != null ? `${r.toFixed(1)} (${row.rating_count ?? 0})` : "—",
    },
    {
      title: "更新时间",
      dataIndex: "updated_at",
      width: 170,
      render: (t: string) => (t ? t.replace("T", " ").slice(0, 19) : "—"),
    },
    {
      title: "操作",
      key: "ops",
      width: 150,
      fixed: "right",
      render: (_: unknown, row) => (
        <Space size="small">
          <Link href={`/books/${row.id}`}>
            <Button size="small" icon={<EditOutlined />}>编辑</Button>
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
            {data ? `共 ${data.total} 本` : "加载中..."}
          </div>
        </div>
        <Input.Search
          placeholder="按书名 / 作者 / ISBN 搜索"
          prefix={<SearchOutlined />}
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
