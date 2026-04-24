"use client";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Form, Input } from "antd";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, setToken } from "@/lib/api";

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
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "radial-gradient(1200px 600px at 10% -10%, #eef2ff 0, transparent 60%), radial-gradient(1000px 500px at 90% 110%, #ede9fe 0, transparent 60%), #f6f7fb",
        padding: 24,
      }}
    >
      <Card
        bordered={false}
        style={{
          width: 420,
          boxShadow: "0 20px 60px rgba(15, 23, 42, 0.08), 0 2px 6px rgba(15, 23, 42, 0.06)",
          borderRadius: 16,
        }}
        bodyStyle={{ padding: 32 }}
      >
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div style={{ fontSize: 32 }}>📚</div>
          <h2 style={{ margin: "8px 0 4px", fontWeight: 600 }}>Books Admin</h2>
          <p style={{ color: "#6b7280", margin: 0, fontSize: 13 }}>
            管理你的图书馆 · 扫描 · 元数据 · 封面
          </p>
        </div>
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
            label="用户名"
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="admin"
              autoComplete="username"
              size="large"
            />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
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
            style={{ marginTop: 8 }}
          >
            登录
          </Button>
        </Form>
      </Card>
    </div>
  );
}
