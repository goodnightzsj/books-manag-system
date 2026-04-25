"use client";
import {
  AppstoreOutlined,
  BookOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RadarChartOutlined,
  ReadOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import {
  Card,
  Col,
  List,
  Progress,
  Row,
  Skeleton,
  Statistic,
  Typography,
  message,
} from "antd";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Job = {
  id: string;
  status: string;
  job_type: string;
  requested_path: string;
  total_items: number;
  processed_items: number;
  success_items: number;
  failed_items: number;
  created_at: string;
};

type Trending = {
  id: string;
  title: string;
  author?: string | null;
  cover_url?: string | null;
  rating?: number | null;
};

const ICON_STYLE = { color: "var(--ink-soft)", fontSize: 18 } as const;

function StatCard({
  title,
  value,
  suffix,
  icon,
  loading,
  footer,
}: {
  title: string;
  value: number | string;
  suffix?: React.ReactNode;
  icon: React.ReactNode;
  loading?: boolean;
  footer?: React.ReactNode;
}) {
  return (
    <Card bordered={false} loading={loading} bodyStyle={{ padding: 20 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          color: "var(--ink-faint)",
        }}
      >
        <span className="eyebrow">{title}</span>
        <span style={ICON_STYLE}>{icon}</span>
      </div>
      <Statistic
        value={value}
        suffix={suffix}
        valueStyle={{
          fontFamily: "var(--font-serif)",
          fontWeight: 600,
          fontSize: 30,
          color: "var(--ink)",
          letterSpacing: "-0.01em",
        }}
      />
      {footer && <div style={{ marginTop: 8 }}>{footer}</div>}
    </Card>
  );
}

function statusToTagClass(status: string): string {
  if (status === "completed") return "tag-ok";
  if (status === "failed") return "tag-danger";
  if (status === "partial_success") return "tag-warn";
  if (status === "running" || status === "queued") return "tag-accent";
  return "tag-quiet";
}

function statusLabel(status: string): string {
  switch (status) {
    case "completed":
      return "已完成";
    case "failed":
      return "失败";
    case "partial_success":
      return "部分成功";
    case "running":
      return "运行中";
    case "queued":
      return "已入队";
    default:
      return status;
  }
}

export default function DashboardPage() {
  const [bookTotal, setBookTotal] = useState<number | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [categories, setCategories] = useState<{ id: string }[]>([]);
  const [trending, setTrending] = useState<Trending[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [b, j, c, t] = await Promise.all([
          api.listBooks({ page: 1, page_size: 1 }),
          api.listScanJobs(5),
          api.listCategories(),
          api.trending(6),
        ]);
        if (!alive) return;
        setBookTotal(b.total);
        setJobs(j.items as Job[]);
        setCategories(c as { id: string }[]);
        setTrending(t as Trending[]);
      } catch (e) {
        message.error((e as Error).message);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const jobStats = useMemo(() => {
    const running = jobs.filter((j) =>
      ["running", "queued"].includes(j.status),
    ).length;
    const failed = jobs.reduce((acc, j) => acc + (j.failed_items || 0), 0);
    const processed = jobs.reduce((acc, j) => acc + (j.processed_items || 0), 0);
    return { running, failed, processed };
  }, [jobs]);

  const healthyRate = useMemo(() => {
    const total = jobs.reduce((acc, j) => acc + (j.total_items || 0), 0);
    if (!total) return 100;
    const failed = jobs.reduce((acc, j) => acc + (j.failed_items || 0), 0);
    return Math.round(((total - failed) / total) * 100);
  }, [jobs]);

  const healthColor =
    healthyRate >= 90 ? "var(--ok)" : healthyRate >= 70 ? "var(--warn)" : "var(--danger)";

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>主控台</h1>
          <div className="subtitle">图书馆运行态势 · 最近任务 · 评分榜单</div>
        </div>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}>
          <StatCard
            title="图书总数"
            value={bookTotal ?? 0}
            icon={<BookOutlined />}
            loading={loading}
          />
        </Col>
        <Col xs={12} md={6}>
          <StatCard
            title="分类数量"
            value={categories.length}
            icon={<AppstoreOutlined />}
            loading={loading}
          />
        </Col>
        <Col xs={12} md={6}>
          <StatCard
            title="进行中任务"
            value={jobStats.running}
            icon={<RadarChartOutlined />}
            loading={loading}
          />
        </Col>
        <Col xs={12} md={6}>
          <StatCard
            title="近任务健康度"
            value={healthyRate}
            suffix="%"
            icon={<RiseOutlined />}
            loading={loading}
            footer={
              <Progress
                percent={healthyRate}
                showInfo={false}
                strokeColor={healthColor}
                trailColor="var(--muted)"
                strokeLinecap="butt"
                strokeWidth={4}
              />
            }
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card
            bordered={false}
            title="最近扫描任务"
            extra={
              <Link href="/scanner" style={{ color: "var(--accent)" }}>
                查看全部 →
              </Link>
            }
            loading={loading}
          >
            <List
              dataSource={jobs}
              locale={{
                emptyText: (
                  <div className="empty-state">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                      <rect
                        x="3.5"
                        y="5"
                        width="17"
                        height="14"
                        rx="1"
                        stroke="currentColor"
                        strokeWidth="1.25"
                      />
                      <path
                        d="M3.5 10h17M8 14h4"
                        stroke="currentColor"
                        strokeWidth="1.25"
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="label">还没有任务</div>
                    <div className="hint">在「扫描」页面发起一个目录扫描即可。</div>
                  </div>
                ),
              }}
              renderItem={(j: Job) => {
                const icon =
                  j.status === "completed" ? (
                    <CheckCircleOutlined style={{ color: "var(--ok)", fontSize: 18 }} />
                  ) : j.status === "failed" ? (
                    <CloseCircleOutlined style={{ color: "var(--danger)", fontSize: 18 }} />
                  ) : (
                    <RadarChartOutlined style={{ color: "var(--accent)", fontSize: 18 }} />
                  );
                return (
                  <List.Item
                    actions={[
                      <Link
                        href={`/scanner/jobs/${j.id}`}
                        key="view"
                        style={{ color: "var(--ink-soft)", fontSize: 12.5 }}
                      >
                        查看 →
                      </Link>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={icon}
                      title={
                        <Typography.Text
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: 13,
                            color: "var(--ink)",
                          }}
                        >
                          {j.requested_path}
                        </Typography.Text>
                      }
                      description={
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 10,
                            marginTop: 4,
                            fontSize: 12,
                            color: "var(--ink-faint)",
                          }}
                        >
                          <span className={`ant-tag ${statusToTagClass(j.status)}`}>
                            {statusLabel(j.status)}
                          </span>
                          <span className="numeric">
                            {j.success_items}/{j.total_items} 成功
                          </span>
                          <span aria-hidden style={{ color: "var(--rule)" }}>
                            ·
                          </span>
                          <span className="numeric">
                            {j.created_at?.replace("T", " ").slice(0, 19)}
                          </span>
                        </div>
                      }
                    />
                  </List.Item>
                );
              }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            bordered={false}
            title={
              <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                <ReadOutlined style={{ color: "var(--ink-faint)" }} />
                评分榜单
              </span>
            }
            loading={loading}
          >
            {trending.length === 0 ? (
              <Skeleton active paragraph={{ rows: 3 }} />
            ) : (
              <div>
                {trending.map((b, idx) => (
                  <Link
                    key={b.id}
                    href={`/books/${b.id}`}
                    className="list-row"
                    style={{ textDecoration: "none", color: "inherit" }}
                  >
                    <span
                      className="numeric eyebrow"
                      style={{
                        width: 28,
                        textAlign: "right",
                        color: "var(--ink-faint)",
                        fontSize: 12,
                      }}
                    >
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    {b.cover_url ? (
                      <img
                        src={b.cover_url}
                        alt=""
                        style={{
                          width: 36,
                          height: 50,
                          objectFit: "cover",
                          borderRadius: 3,
                          border: "1px solid var(--rule)",
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          width: 36,
                          height: 50,
                          background: "var(--muted)",
                          color: "var(--ink-soft)",
                          borderRadius: 3,
                          display: "grid",
                          placeItems: "center",
                          fontFamily: "var(--font-serif)",
                          fontWeight: 600,
                        }}
                      >
                        {b.title.slice(0, 1)}
                      </div>
                    )}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: 15,
                          fontWeight: 600,
                          color: "var(--ink)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {b.title}
                      </div>
                      <div
                        style={{
                          fontSize: 11.5,
                          color: "var(--ink-faint)",
                          letterSpacing: "0.04em",
                          marginTop: 2,
                          textTransform: "uppercase",
                        }}
                      >
                        {b.author ?? "—"}
                      </div>
                    </div>
                    {b.rating != null && (
                      <span
                        className="numeric"
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: 15,
                          fontWeight: 600,
                          color: "var(--accent)",
                          minWidth: 44,
                          textAlign: "right",
                        }}
                      >
                        ★ {b.rating.toFixed(1)}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </AppShell>
  );
}
