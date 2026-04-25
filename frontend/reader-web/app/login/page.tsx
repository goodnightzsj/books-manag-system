"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";
import { BrandMark } from "@/components/BrandMark";
import { ErrorBanner } from "@/components/ErrorBanner";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
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
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            marginBottom: 18,
          }}
        >
          <BrandMark size={40} />
        </div>
        <span
          className="eyebrow"
          style={{ display: "block", textAlign: "center" }}
        >
          登录
        </span>
        <h1
          className="no-rule"
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 32,
            fontWeight: 600,
            letterSpacing: "-0.012em",
            margin: "10px 0 6px",
            paddingLeft: 0,
            color: "var(--ink)",
            lineHeight: 1.15,
            textAlign: "center",
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
            textAlign: "center",
          }}
        >
          使用账号密码继续阅读。
        </p>

        {error && (
          <div style={{ margin: "20px 0 0" }}>
            <ErrorBanner
              title="登录失败"
              description={error}
              onRetry={() => setError(null)}
              retryLabel="清除"
            />
          </div>
        )}

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
            <div style={{ position: "relative" }}>
              <input
                className="input"
                type={showPwd ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                aria-label={showPwd ? "隐藏密码" : "显示密码"}
                onClick={() => setShowPwd((v) => !v)}
                style={{
                  position: "absolute",
                  right: 8,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: 0,
                  cursor: "pointer",
                  color: "var(--ink-faint)",
                  padding: 6,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {showPwd ? (
                  // eye-off
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M3 3l18 18M10.6 10.6a2 2 0 102.8 2.8M9.9 5.1A11 11 0 0112 5c5 0 9 4 10 7-0.5 1.4-1.6 3.1-3.2 4.5M6.2 6.2C4.2 7.6 2.7 9.6 2 12c1 3 5 7 10 7 1.6 0 3-0.3 4.3-0.9"
                      stroke="currentColor"
                      strokeWidth="1.4"
                      strokeLinecap="round"
                    />
                  </svg>
                ) : (
                  // eye
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"
                      stroke="currentColor"
                      strokeWidth="1.4"
                      strokeLinecap="round"
                    />
                    <circle cx="12" cy="12" r="2.6" stroke="currentColor" strokeWidth="1.4" />
                  </svg>
                )}
              </button>
            </div>
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
