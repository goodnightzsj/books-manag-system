"use client";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Input } from "antd";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, setToken } from "@/lib/api";

/**
 * Decorative pattern for the brand panel — a subtle stack of paper
 * "card index" rules. SVG only, so it scales and stays crisp on 4K.
 * No glassmorphism, no halo: just hairlines and a single warm tint.
 */
function CardIndexPattern() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 360 480"
      style={{
        width: "100%",
        height: "100%",
        position: "absolute",
        inset: 0,
        opacity: 0.55,
        color: "var(--rule)",
      }}
    >
      <defs>
        <pattern
          id="cardlines"
          width="360"
          height="32"
          patternUnits="userSpaceOnUse"
        >
          <line
            x1="0"
            y1="31.5"
            x2="360"
            y2="31.5"
            stroke="currentColor"
            strokeWidth="1"
          />
        </pattern>
      </defs>
      <rect width="360" height="480" fill="url(#cardlines)" />
      {/* Three offset "cards" suggesting an open card catalog drawer. */}
      <g stroke="var(--rule)" fill="var(--surface)">
        <rect x="36" y="60" width="220" height="120" rx="2" />
        <rect x="60" y="120" width="220" height="120" rx="2" />
        <rect x="84" y="180" width="220" height="120" rx="2" />
      </g>
      <g
        fill="none"
        stroke="var(--accent)"
        strokeWidth="1.25"
        opacity="0.55"
      >
        <line x1="60" y1="138" x2="220" y2="138" />
        <line x1="60" y1="156" x2="180" y2="156" />
        <line x1="84" y1="200" x2="244" y2="200" />
        <line x1="84" y1="218" x2="200" y2="218" />
      </g>
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onFinish(values: { username: string; password: string }) {
    setLoading(true);
    setError(null);
    try {
      const r = await api.login(values.username, values.password);
      setToken(r.access_token);
      router.push("/dashboard");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "minmax(0, 1.05fr) minmax(0, 1fr)",
        background: "var(--paper-cool)",
      }}
    >
      {/* Left: brand panel */}
      <aside
        style={{
          position: "relative",
          padding: "56px 64px",
          background: "var(--paper)",
          borderRight: "1px solid var(--rule)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          overflow: "hidden",
          minHeight: "100vh",
        }}
      >
        <CardIndexPattern />
        <div style={{ position: "relative", zIndex: 1 }}>
          <span className="eyebrow">books management system</span>
          <h1
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 88,
              lineHeight: 0.96,
              fontWeight: 600,
              letterSpacing: "-0.025em",
              margin: "16px 0 0",
              color: "var(--ink)",
            }}
          >
            books<span style={{ color: "var(--accent)" }}>.</span>
          </h1>
          <p
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 19,
              lineHeight: 1.55,
              color: "var(--ink-soft)",
              maxWidth: 360,
              marginTop: 28,
              fontStyle: "italic",
            }}
          >
            把每一页都收进档案。
            <br />
            Catalog every page. Scan. Index. Read.
          </p>
        </div>
        <div
          style={{
            position: "relative",
            zIndex: 1,
            display: "flex",
            gap: 24,
            fontSize: 11,
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: "var(--ink-faint)",
            fontWeight: 500,
          }}
        >
          <span>vol. 01</span>
          <span aria-hidden>—</span>
          <span>archive edition</span>
        </div>
      </aside>

      {/* Right: form */}
      <main
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "48px 56px",
        }}
      >
        <div style={{ width: "100%", maxWidth: 380 }}>
          <span className="eyebrow">登录</span>
          <h2
            style={{
              fontFamily: "var(--font-serif)",
              fontSize: 28,
              fontWeight: 600,
              letterSpacing: "-0.01em",
              margin: "8px 0 6px",
              color: "var(--ink)",
            }}
          >
            进入管理后台
          </h2>
          <p
            style={{
              color: "var(--ink-soft)",
              fontSize: 13,
              margin: "0 0 28px",
              lineHeight: 1.6,
            }}
          >
            管理你的图书馆 · 扫描 · 元数据 · 封面
          </p>

          {error && (
            <Alert
              type="error"
              showIcon
              message={error}
              style={{ marginBottom: 16 }}
            />
          )}
          <Form
            layout="vertical"
            initialValues={{ username: "admin" }}
            onFinish={onFinish}
            requiredMark={false}
          >
            <Form.Item
              label={<span className="eyebrow">用户名</span>}
              name="username"
              rules={[{ required: true, message: "请输入用户名" }]}
            >
              <Input
                prefix={<UserOutlined style={{ color: "var(--ink-faint)" }} />}
                placeholder="admin"
                autoComplete="username"
                size="large"
              />
            </Form.Item>
            <Form.Item
              label={<span className="eyebrow">密码</span>}
              name="password"
              rules={[{ required: true, message: "请输入密码" }]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: "var(--ink-faint)" }} />}
                placeholder="••••••"
                autoComplete="current-password"
                size="large"
              />
            </Form.Item>
            <Button
              htmlType="submit"
              type="primary"
              block
              size="large"
              loading={loading}
              style={{ marginTop: 8, height: 44 }}
            >
              登录
            </Button>
          </Form>

          <hr className="hairline" style={{ margin: "32px 0 16px" }} />
          <div
            style={{
              fontSize: 11,
              letterSpacing: "0.06em",
              color: "var(--ink-faint)",
              lineHeight: 1.7,
            }}
          >
            默认凭据由部署侧分发；未持有凭据请联系管理员。
          </div>
        </div>
      </main>
    </div>
  );
}
