"use client";
import {
  BookOutlined,
  CheckCircleTwoTone,
  CloseCircleTwoTone,
  FireOutlined,
  RadarChartOutlined,
  RiseOutlined,
  TagsOutlined,
} from "@ant-design/icons";
import {
  Avatar,
  Card,
  Col,
  List,
  Progress,
  Row,
  Skeleton,
  Statistic,
  Tag,
  Typography,
  message,
} from "antd";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [books, setBooks] = useState<{ items: any[]; total: number } | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [trending, setTrending] = useState<any[]>([]);
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
        setBooks({ items: [], total: b.total });
        setJobs(j.items);
        setCategories(c as any[]);
        setTrending(t);
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

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <div className="subtitle">图书馆运行态势 · 最近任务 · 推荐榜单</div>
        </div>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}>
          <Card bordered={false} loading={loading}>
            <Statistic
              title={<span style={{ color: "#6b7280" }}>图书总数</span>}
              value={books?.total ?? 0}
              prefix={<BookOutlined style={{ color: "#4F46E5" }} />}
              valueStyle={{ fontWeight: 600, fontSize: 26 }}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card bordered={false} loading={loading}>
            <Statistic
              title={<span style={{ color: "#6b7280" }}>分类数量</span>}
              value={categories.length}
              prefix={<TagsOutlined style={{ color: "#10B981" }} />}
              valueStyle={{ fontWeight: 600, fontSize: 26 }}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card bordered={false} loading={loading}>
            <Statistic
              title={<span style={{ color: "#6b7280" }}>进行中任务</span>}
              value={jobStats.running}
              prefix={<RadarChartOutlined style={{ color: "#F59E0B" }} />}
              valueStyle={{ fontWeight: 600, fontSize: 26 }}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card bordered={false} loading={loading}>
            <Statistic
              title={<span style={{ color: "#6b7280" }}>近任务健康度</span>}
              value={healthyRate}
              suffix="%"
              prefix={<RiseOutlined style={{ color: "#8B5CF6" }} />}
              valueStyle={{ fontWeight: 600, fontSize: 26 }}
            />
            <Progress
              percent={healthyRate}
              showInfo={false}
              strokeColor={healthyRate >= 80 ? "#10B981" : "#F59E0B"}
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card
            bordered={false}
            title="最近扫描任务"
            extra={<Link href="/scanner">查看全部</Link>}
            loading={loading}
          >
            <List
              dataSource={jobs}
              locale={{ emptyText: "暂无任务" }}
              renderItem={(j: any) => (
                <List.Item
                  actions={[
                    <Link href={`/scanner/jobs/${j.id}`} key="view">
                      查看
                    </Link>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      j.status === "completed" ? (
                        <CheckCircleTwoTone
                          twoToneColor="#10B981"
                          style={{ fontSize: 24 }}
                        />
                      ) : j.status === "failed" ? (
                        <CloseCircleTwoTone
                          twoToneColor="#EF4444"
                          style={{ fontSize: 24 }}
                        />
                      ) : (
                        <RadarChartOutlined style={{ fontSize: 24, color: "#4F46E5" }} />
                      )
                    }
                    title={
                      <Typography.Text code style={{ fontSize: 13 }}>
                        {j.requested_path}
                      </Typography.Text>
                    }
                    description={
                      <div>
                        <Tag>{j.job_type}</Tag>
                        <Tag color="blue">{j.status}</Tag>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          {j.success_items}/{j.total_items} 成功 ·{" "}
                          {j.created_at?.replace("T", " ").slice(0, 19)}
                        </Typography.Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            bordered={false}
            title={
              <span>
                <FireOutlined style={{ color: "#F97316", marginRight: 8 }} />
                评分 Top
              </span>
            }
            loading={loading}
          >
            {trending.length === 0 ? (
              <Skeleton active paragraph={{ rows: 3 }} />
            ) : (
              <List
                dataSource={trending}
                renderItem={(b: any, idx: number) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        b.cover_url ? (
                          <Avatar
                            shape="square"
                            size={44}
                            src={b.cover_url}
                            style={{ borderRadius: 6 }}
                          />
                        ) : (
                          <Avatar
                            shape="square"
                            size={44}
                            style={{
                              borderRadius: 6,
                              background: "#eef2ff",
                              color: "#4F46E5",
                              fontWeight: 600,
                            }}
                          >
                            {idx + 1}
                          </Avatar>
                        )
                      }
                      title={
                        <Link href={`/books/${b.id}`}>
                          <Typography.Text strong>{b.title}</Typography.Text>
                        </Link>
                      }
                      description={
                        <div style={{ fontSize: 12 }}>
                          <Typography.Text type="secondary">
                            {b.author ?? "?"}
                          </Typography.Text>
                          {b.rating != null && (
                            <Tag style={{ marginLeft: 8 }} color="gold">
                              ★ {b.rating.toFixed(1)}
                            </Tag>
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </AppShell>
  );
}
