"use client";
import {
  CheckCircleTwoTone,
  ClockCircleTwoTone,
  CloseCircleTwoTone,
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
  Tag,
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
      <Tag icon={<CheckCircleTwoTone twoToneColor="#10B981" />} color="success">
        已完成
      </Tag>
    );
  if (status === "running" || status === "queued")
    return (
      <Tag icon={<SyncOutlined spin />} color="processing">
        {status === "queued" ? "已入队" : "运行中"}
      </Tag>
    );
  if (status === "failed")
    return (
      <Tag icon={<CloseCircleTwoTone twoToneColor="#EF4444" />} color="error">
        失败
      </Tag>
    );
  if (status === "partial_success")
    return (
      <Tag icon={<ClockCircleTwoTone twoToneColor="#F59E0B" />} color="warning">
        部分成功
      </Tag>
    );
  return <Tag>{status}</Tag>;
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
    { title: "类型", dataIndex: "job_type", width: 130, render: (v) => <Tag>{v}</Tag> },
    { title: "状态", dataIndex: "status", width: 130, render: (v) => <StatusTag status={v} /> },
    {
      title: "路径",
      dataIndex: "requested_path",
      ellipsis: true,
      render: (v: string) => <Typography.Text code>{v}</Typography.Text>,
    },
    {
      title: "进度",
      width: 220,
      render: (_: unknown, row) => {
        const pct = row.total_items ? Math.round((row.processed_items / row.total_items) * 100) : 0;
        return (
          <Space size="small" style={{ width: "100%" }}>
            <Progress
              percent={pct}
              size="small"
              status={
                row.status === "failed"
                  ? "exception"
                  : row.status === "completed"
                  ? "success"
                  : "active"
              }
              style={{ minWidth: 100, marginBottom: 0 }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {row.processed_items}/{row.total_items}
            </Typography.Text>
          </Space>
        );
      },
    },
    {
      title: "OK / 失败",
      width: 120,
      render: (_: unknown, row) => (
        <Space size="small">
          <Tag color="green">{row.success_items}</Tag>
          <Tag color="red">{row.failed_items}</Tag>
        </Space>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      width: 160,
      render: (t: string) => (t ? t.replace("T", " ").slice(0, 19) : "—"),
    },
    {
      title: "操作",
      key: "ops",
      width: 90,
      fixed: "right",
      render: (_: unknown, row) => (
        <Link href={`/scanner/jobs/${row.id}`}>
          <Button size="small" type="link">查看</Button>
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
        <Form layout="inline" onFinish={onScan} style={{ gap: 8, flexWrap: "wrap" }}>
          <Form.Item
            name="directory"
            rules={[{ required: true, message: "请填写目录路径" }]}
            style={{ flex: 1, minWidth: 360 }}
          >
            <Input
              prefix={<FolderOpenOutlined />}
              placeholder="/app/books/incoming"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              size="large"
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

      {error && <Alert style={{ marginBottom: 16 }} type="error" showIcon message={error} />}

      <Card bordered={false} title="最近任务">
        <Table<Job>
          rowKey="id"
          dataSource={jobs}
          columns={columns}
          pagination={false}
          size="middle"
          scroll={{ x: 1000 }}
        />
      </Card>
    </AppShell>
  );
}
