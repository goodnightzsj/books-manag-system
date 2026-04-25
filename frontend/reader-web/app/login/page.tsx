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
        background: "var(--bg-paper)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          background: "var(--bg-surface)",
          border: "1px solid var(--rule)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-md)",
          padding: "40px 36px 32px",
        }}
      >
        <span className="eyebrow">登录</span>
        <h1
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 32,
            fontWeight: 600,
            letterSpacing: "-0.012em",
            margin: "10px 0 6px",
            paddingLeft: 0,
            color: "var(--ink)",
            lineHeight: 1.15,
          }}
        >
          回到你的书房
        </h1>
        <p
          style={{
            color: "var(--ink-soft)",
            fontFamily: "var(--font-serif)",
            fontSize: 15,
            fontStyle: "italic",
            margin: 0,
          }}
        >
          使用账号密码继续阅读。
        </p>

        {error && <div className="error" style={{ margin: "16px 0" }}>{error}</div>}

        <form
          onSubmit={onSubmit}
          style={{ display: "grid", gap: 14, marginTop: 24 }}
        >
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
            style={{
              justifyContent: "center",
              padding: "12px 18px",
              marginTop: 8,
              fontSize: 14,
            }}
          >
            {busy ? "登录中…" : "进入书架"}
          </button>
        </form>

        <hr
          style={{
            border: 0,
            borderTop: "1px solid var(--rule)",
            margin: "28px 0 14px",
          }}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: "var(--font-sans)",
            fontSize: 11,
            color: "var(--ink-faint)",
            letterSpacing: "0.16em",
            textTransform: "uppercase",
          }}
        >
          <span>books<span style={{ color: "var(--accent)" }}>.</span></span>
          <span>reader edition</span>
        </div>
      </div>
    </div>
  );
}
