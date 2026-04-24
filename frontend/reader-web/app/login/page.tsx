"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.login(username, password);
      setToken(r.access_token);
      router.push("/library");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background:
          "radial-gradient(900px 500px at 15% 20%, rgba(179,74,44,0.12), transparent 55%), radial-gradient(800px 400px at 90% 80%, rgba(120,80,40,0.10), transparent 50%), var(--bg-paper)",
      }}
    >
      <div
        className="card"
        style={{
          width: 420,
          boxShadow: "var(--shadow-lg)",
          padding: "36px 32px",
        }}
      >
        <div className="eyebrow">登录</div>
        <h1 style={{ marginTop: 4, marginBottom: 4 }}>回到你的书房</h1>
        <p style={{ color: "var(--ink-soft)", fontFamily: "var(--font-sans)", fontSize: 13 }}>
          使用账号密码继续阅读。
        </p>
        {error && <div className="error" style={{ margin: "12px 0" }}>{error}</div>}
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 14, marginTop: 18 }}>
          <label style={{ display: "grid", gap: 6 }}>
            <span className="eyebrow">用户名</span>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label style={{ display: "grid", gap: 6 }}>
            <span className="eyebrow">密码</span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="btn primary"
            style={{ justifyContent: "center", padding: "12px 18px", marginTop: 8 }}
          >
            {busy ? "登录中…" : "进入书架"}
          </button>
        </form>
      </div>
    </div>
  );
}
