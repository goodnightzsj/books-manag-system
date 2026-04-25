"use client";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  FolderOpenOutlined,
  PlayCircleOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Progress,
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

type Job = {
  id: string;
  job_type: string;
  status: string;
  requested_path: string;
  total_items: number;
  processed_items: number;
  success_items: number;
  failed_items: number;
  created_at: string;
};

function StatusTag({ status }: { status: string }) {
  if (status === "completed")
    return (
      <span className="ant-tag tag-ok">
        <CheckCircleOutlined style={{ marginRight: 4 }} />
        已完成
      </span>
    );
  if (status === "running" || status === "queued")
    return (
      <span className="ant-tag tag-accent">
        <SyncOutlined spin style={{ marginRight: 4 }} />
        {status === "queued" ? "已入队" : "运行中"}
      </span>
    );
  if (status === "failed")
    return (
      <span className="ant-tag tag-danger">
        <CloseCircleOutlined style={{ marginRight: 4 }} />
        失败
      </span>
    );
  if (status === "partial_success")
    return (
      <span className="ant-tag tag-warn">
        <ClockCircleOutlined style={{ marginRight: 4 }} />
        部分成功
      </span>
    );
  return <span className="ant-tag tag-quiet">{status}</span>;
}

function EmptyJobs() {
  return (
    <div className="empty-state">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
        <circle
          cx="12"
          cy="12"
          r="8"
          stroke="currentColor"
          strokeWidth="1.25"
        />
        <path
          d="M12 8v4l2.5 2"
          stroke="currentColor"
          strokeWidth="1.25"
          strokeLinecap="round"
        />
      </svg>
      <div className="label">还没有扫描任务</div>
      <div className="hint">在上方输入目录路径，点击「发起扫描」即可入队。</div>
    </div>
  );
}

export default function ScannerPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [directory, setDirectory] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await api.listScanJobs();
      setJobs(r.items as Job[]);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  async function onScan(values: { directory: string }) {
    setLoading(true);
    try {
      await api.startDirectoryScan(values.directory.trim());
      message.success("扫描任务已入队");
      setDirectory("");
      load();
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const columns: ColumnsType<Job> = [
    {
      title: "类型",
      dataIndex: "job_type",
      width: 120,
      render: (v: string) => <span className="ant-tag tag-quiet">{v}</span>,
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 130,
      render: (v: string) => <StatusTag status={v} />,
    },
    {
      title: "路径",
      dataIndex: "requested_path",
      ellipsis: true,
      render: (v: string) => (
        <Typography.Text
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 12.5,
            color: "var(--ink)",
          }}
        >
          {v}
        </Typography.Text>
      ),
    },
    {
      title: "进度",
      width: 220,
      render: (_: unknown, row) => {
        const pct = row.total_items
          ? Math.round((row.processed_items / row.total_items) * 100)
          : 0;
        const stroke =
          row.status === "failed"
            ? "var(--danger)"
            : row.status === "completed"
            ? "var(--ok)"
            : "var(--accent)";
        return (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Progress
              percent={pct}
              strokeWidth={4}
              strokeColor={stroke}
              trailColor="var(--muted)"
              strokeLinecap="butt"
              showInfo={false}
              style={{ flex: 1, marginBottom: 0 }}
            />
            <span
              className="numeric"
              style={{ fontSize: 12, color: "var(--ink-soft)", minWidth: 56 }}
            >
              {row.processed_items}/{row.total_items}
            </span>
          </div>
        );
      },
    },
    {
      title: "OK / 失败",
      width: 130,
      render: (_: unknown, row) => (
        <Space size={6}>
          <span className="ant-tag tag-ok numeric">{row.success_items}</span>
          <span className="ant-tag tag-danger numeric">{row.failed_items}</span>
        </Space>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      width: 160,
      render: (t: string) => (
        <span className="numeric" style={{ color: "var(--ink-soft)", fontSize: 12.5 }}>
          {t ? t.replace("T", " ").slice(0, 19) : "—"}
        </span>
      ),
    },
    {
      title: "操作",
      key: "ops",
      width: 80,
      fixed: "right",
      render: (_: unknown, row) => (
        <Link href={`/scanner/jobs/${row.id}`}>
          <Button size="small" type="link" style={{ paddingInline: 0 }}>
            查看 →
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>扫描任务</h1>
          <div className="subtitle">在 BOOKS_DIR 内选定目录发起后台扫描</div>
        </div>
      </div>

      <Card bordered={false} style={{ marginBottom: 16 }}>
        <Form layout="inline" onFinish={onScan} style={{ gap: 12, flexWrap: "wrap" }}>
          <Form.Item
            name="directory"
            rules={[{ required: true, message: "请填写目录路径" }]}
            style={{ flex: 1, minWidth: 360 }}
          >
            <Input
              prefix={
                <FolderOpenOutlined style={{ color: "var(--ink-faint)" }} />
              }
              placeholder="/app/books/incoming"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              size="large"
              style={{ fontFamily: "var(--font-mono)" }}
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              size="large"
              htmlType="submit"
              loading={loading}
              icon={<PlayCircleOutlined />}
            >
              发起扫描
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {error && (
        <Alert style={{ marginBottom: 16 }} type="error" showIcon message={error} />
      )}

      <Card bordered={false} title="最近任务">
        <Table<Job>
          rowKey="id"
          dataSource={jobs}
          columns={columns}
          pagination={false}
          size="middle"
          scroll={{ x: 1000 }}
          locale={{ emptyText: <EmptyJobs /> }}
        />
      </Card>
    </AppShell>
  );
}
