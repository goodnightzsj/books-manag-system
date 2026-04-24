"use client";
import { ReloadOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Progress,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Item = {
  id: string;
  file_path: string;
  file_format?: string | null;
  status: string;
  book_id?: string | null;
  error_message?: string | null;
};

const itemTagColor: Record<string, string> = {
  created: "green",
  updated: "blue",
  skipped: "default",
  failed: "red",
  queued: "gold",
  processing: "processing",
};

export default function ScanJobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;
  const [job, setJob] = useState<any>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [j, it] = await Promise.all([api.getScanJob(id), api.listScanJobItems(id)]);
      setJob(j);
      setItems(it.items as Item[]);
    } catch (e) {
      message.error((e as Error).message);
    }
  }, [id]);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  const failed = items.filter((i) => i.status === "failed");
  const pct = job?.total_items ? Math.round((job.processed_items / job.total_items) * 100) : 0;

  async function onRetry() {
    setLoading(true);
    try {
      await api.retryFailed(id);
      message.success(`已重试 ${failed.length} 个失败项`);
      load();
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const columns: ColumnsType<Item> = [
    {
      title: "状态",
      dataIndex: "status",
      width: 120,
      render: (s: string) => <Tag color={itemTagColor[s] ?? "default"}>{s}</Tag>,
    },
    {
      title: "格式",
      dataIndex: "file_format",
      width: 90,
      render: (f: string | null) => (f ? <Tag>{f.toUpperCase()}</Tag> : "—"),
    },
    {
      title: "路径",
      dataIndex: "file_path",
      ellipsis: true,
      render: (v: string) => <Typography.Text code>{v}</Typography.Text>,
    },
    {
      title: "错误信息",
      dataIndex: "error_message",
      width: 320,
      render: (e: string | null) => (e ? <Typography.Text type="danger">{e}</Typography.Text> : "—"),
    },
  ];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>扫描任务详情</h1>
          <div className="subtitle">Job {id.slice(0, 8)}…</div>
        </div>
        <Space>
          <Button onClick={() => router.back()}>返回</Button>
          {failed.length > 0 && (
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={onRetry}
            >
              重试 {failed.length} 个失败项
            </Button>
          )}
        </Space>
      </div>

      {job && (
        <>
          <Card bordered={false} style={{ marginBottom: 16 }}>
            <Descriptions column={{ xs: 1, sm: 2, md: 3 }} size="small">
              <Descriptions.Item label="类型">{job.job_type}</Descriptions.Item>
              <Descriptions.Item label="状态"><Tag>{job.status}</Tag></Descriptions.Item>
              <Descriptions.Item label="路径">
                <Typography.Text code>{job.requested_path}</Typography.Text>
              </Descriptions.Item>
              <Descriptions.Item label="总数">{job.total_items}</Descriptions.Item>
              <Descriptions.Item label="成功">{job.success_items}</Descriptions.Item>
              <Descriptions.Item label="失败">{job.failed_items}</Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {job.created_at?.replace("T", " ").slice(0, 19)}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {job.started_at?.replace("T", " ").slice(0, 19) ?? "—"}
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {job.finished_at?.replace("T", " ").slice(0, 19) ?? "—"}
              </Descriptions.Item>
            </Descriptions>
            <Progress
              percent={pct}
              status={
                job.status === "failed"
                  ? "exception"
                  : job.status === "completed"
                  ? "success"
                  : "active"
              }
              style={{ marginTop: 12 }}
            />
          </Card>

          <Card bordered={false} title={`项目 (${items.length})`}>
            <Table<Item>
              rowKey="id"
              dataSource={items}
              columns={columns}
              size="middle"
              scroll={{ x: 900 }}
              pagination={{ pageSize: 20, showSizeChanger: true }}
            />
          </Card>
        </>
      )}
    </AppShell>
  );
}
