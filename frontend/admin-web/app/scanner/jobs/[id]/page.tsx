"use client";
import { ReloadOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Progress,
  Space,
  Table,
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

const ITEM_TAG: Record<string, string> = {
  created: "tag-ok",
  updated: "tag-accent",
  skipped: "tag-quiet",
  failed: "tag-danger",
  queued: "tag-warn",
  processing: "tag-accent",
};

const ITEM_LABEL: Record<string, string> = {
  created: "新建",
  updated: "更新",
  skipped: "跳过",
  failed: "失败",
  queued: "入队",
  processing: "处理中",
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
      const [j, it] = await Promise.all([
        api.getScanJob(id),
        api.listScanJobItems(id),
      ]);
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
  const pct = job?.total_items
    ? Math.round((job.processed_items / job.total_items) * 100)
    : 0;

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
      width: 110,
      render: (s: string) => (
        <span className={`ant-tag ${ITEM_TAG[s] ?? "tag-quiet"}`}>
          {ITEM_LABEL[s] ?? s}
        </span>
      ),
    },
    {
      title: "格式",
      dataIndex: "file_format",
      width: 80,
      render: (f: string | null) =>
        f ? <span className="ant-tag tag-quiet">{f.toUpperCase()}</span> : "—",
    },
    {
      title: "路径",
      dataIndex: "file_path",
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
      title: "错误信息",
      dataIndex: "error_message",
      width: 320,
      render: (e: string | null) =>
        e ? (
          <Typography.Text
            style={{ color: "var(--danger)", fontSize: 12.5 }}
          >
            {e}
          </Typography.Text>
        ) : (
          <span style={{ color: "var(--ink-faint)" }}>—</span>
        ),
    },
  ];

  const stroke =
    job?.status === "failed"
      ? "var(--danger)"
      : job?.status === "completed"
      ? "var(--ok)"
      : "var(--accent)";

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>扫描任务详情</h1>
          <div className="subtitle">
            Job{" "}
            <span
              className="numeric"
              style={{ fontFamily: "var(--font-mono)", color: "var(--ink-soft)" }}
            >
              {id.slice(0, 8)}…
            </span>
          </div>
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
            <Descriptions
              column={{ xs: 1, sm: 2, md: 3 }}
              size="small"
              labelStyle={{ color: "var(--ink-faint)" }}
            >
              <Descriptions.Item label="类型">{job.job_type}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <span className="ant-tag tag-quiet">{job.status}</span>
              </Descriptions.Item>
              <Descriptions.Item label="路径">
                <Typography.Text
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 12.5,
                  }}
                >
                  {job.requested_path}
                </Typography.Text>
              </Descriptions.Item>
              <Descriptions.Item label="总数">
                <span className="numeric">{job.total_items}</span>
              </Descriptions.Item>
              <Descriptions.Item label="成功">
                <span className="numeric" style={{ color: "var(--ok)" }}>
                  {job.success_items}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="失败">
                <span className="numeric" style={{ color: "var(--danger)" }}>
                  {job.failed_items}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                <span className="numeric" style={{ color: "var(--ink-soft)" }}>
                  {job.created_at?.replace("T", " ").slice(0, 19)}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                <span className="numeric" style={{ color: "var(--ink-soft)" }}>
                  {job.started_at?.replace("T", " ").slice(0, 19) ?? "—"}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                <span className="numeric" style={{ color: "var(--ink-soft)" }}>
                  {job.finished_at?.replace("T", " ").slice(0, 19) ?? "—"}
                </span>
              </Descriptions.Item>
            </Descriptions>
            <Progress
              percent={pct}
              strokeColor={stroke}
              trailColor="var(--muted)"
              strokeLinecap="butt"
              strokeWidth={4}
              showInfo={false}
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
              locale={{
                emptyText: (
                  <div className="empty-state">
                    <div className="label">暂无项目</div>
                    <div className="hint">扫描器还未发现任何文件。</div>
                  </div>
                ),
              }}
            />
          </Card>
        </>
      )}
    </AppShell>
  );
}
