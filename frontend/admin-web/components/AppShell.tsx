"use client";
import {
  BookOutlined,
  DashboardOutlined,
  FolderOpenOutlined,
  LogoutOutlined,
  RadarChartOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Avatar, Breadcrumb, Button, Dropdown, Layout, Menu } from "antd";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { clearToken, getToken, api } from "@/lib/api";

const { Header, Sider, Content } = Layout;

type MenuKey = "/dashboard" | "/books" | "/scanner" | "/categories";

const menuItems = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: <Link href="/dashboard">概览</Link>,
    crumb: "概览",
  },
  {
    key: "/books",
    icon: <BookOutlined />,
    label: <Link href="/books">图书</Link>,
    crumb: "图书",
  },
  {
    key: "/scanner",
    icon: <RadarChartOutlined />,
    label: <Link href="/scanner">扫描</Link>,
    crumb: "扫描任务",
  },
  {
    key: "/categories",
    icon: <FolderOpenOutlined />,
    label: <Link href="/categories">分类</Link>,
    crumb: "分类",
  },
] as const satisfies ReadonlyArray<{
  key: MenuKey;
  icon: React.ReactNode;
  label: React.ReactNode;
  crumb: string;
}>;

/**
 * Brand lockup.
 *
 * Lowercase serif `books.` with the terminal period in terracotta. Subtitle
 * sans-caps below in collapsed-letterspaced form. The whole assembly is inert
 * (no link wrapping) since the sider already has a Dashboard menu entry; the
 * lockup is identity, not navigation, and conflating the two reads as
 * "default template".
 */
function BrandLockup({ collapsed }: { collapsed: boolean }) {
  if (collapsed) {
    return (
      <div
        aria-label="Books admin"
        style={{
          fontFamily: "var(--font-serif)",
          color: "#F5F4EE",
          fontSize: 22,
          fontWeight: 600,
          letterSpacing: "-0.02em",
        }}
      >
        b<span style={{ color: "var(--accent)" }}>.</span>
      </div>
    );
  }
  return (
    <div style={{ display: "grid", gap: 2, lineHeight: 1.1 }}>
      <span
        style={{
          fontFamily: "var(--font-serif)",
          color: "#F5F4EE",
          fontSize: 22,
          fontWeight: 600,
          letterSpacing: "-0.01em",
        }}
      >
        books<span style={{ color: "var(--accent)" }}>.</span>
      </span>
      <span
        style={{
          fontFamily: "var(--font-sans)",
          color: "rgba(245, 244, 238, 0.55)",
          fontSize: 10.5,
          fontWeight: 500,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
        }}
      >
        管理后台
      </span>
    </div>
  );
}

function deriveCrumbs(pathname: string) {
  const top = menuItems.find((m) => pathname.startsWith(m.key));
  const crumbs: { title: React.ReactNode; href?: string }[] = [
    { title: <Link href="/dashboard">主控台</Link> },
  ];
  if (top) {
    crumbs.push({ title: <Link href={top.key}>{top.crumb}</Link> });
  }
  // Detail routes: /books/[id], /scanner/jobs/[id]
  const segments = pathname.split("/").filter(Boolean);
  if (top?.key === "/books" && segments[1]) {
    crumbs.push({ title: "详情" });
  } else if (top?.key === "/scanner" && segments[1] === "jobs" && segments[2]) {
    crumbs.push({ title: `任务 ${segments[2].slice(0, 8)}…` });
  }
  return crumbs;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname() ?? "/dashboard";

  const [collapsed, setCollapsed] = useState(false);
  const [username, setUsername] = useState<string>("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .me()
      .then((u) => setUsername(u.username))
      .catch(() => {
        clearToken();
        router.replace("/login");
      });
  }, [router]);

  const selectedKey = useMemo(() => {
    const found = menuItems.find((m) => pathname.startsWith(m.key));
    return found?.key ?? "/dashboard";
  }, [pathname]);

  const crumbs = useMemo(() => deriveCrumbs(pathname), [pathname]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        theme="dark"
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={232}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            paddingInline: collapsed ? 0 : 22,
            justifyContent: collapsed ? "center" : "flex-start",
            borderBottom: "1px solid #2a2823",
          }}
        >
          <BrandLockup collapsed={collapsed} />
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems.map(({ crumb: _crumb, ...item }) => item)}
          style={{ borderInlineEnd: "none", paddingTop: 12 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "var(--surface)",
            borderBottom: "1px solid var(--rule)",
            display: "flex",
            alignItems: "center",
            gap: 16,
            paddingInline: 24,
          }}
        >
          <Breadcrumb items={crumbs} style={{ fontSize: 13 }} />
          <div style={{ flex: 1 }} />
          <Dropdown
            placement="bottomRight"
            menu={{
              items: [
                {
                  key: "user",
                  label: (
                    <div style={{ padding: "4px 4px 8px", borderBottom: "1px solid var(--rule)" }}>
                      <div style={{ fontWeight: 600, color: "var(--ink)" }}>
                        {username || "admin"}
                      </div>
                      <div
                        style={{
                          fontSize: 11,
                          color: "var(--ink-faint)",
                          letterSpacing: "0.06em",
                          textTransform: "uppercase",
                          marginTop: 2,
                        }}
                      >
                        管理员
                      </div>
                    </div>
                  ),
                  disabled: true,
                  style: { cursor: "default" },
                },
                {
                  key: "logout",
                  icon: <LogoutOutlined />,
                  label: "退出登录",
                  onClick: logout,
                },
              ],
            }}
          >
            <Button
              type="text"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                paddingInline: 8,
                height: 36,
              }}
            >
              <Avatar
                size={28}
                icon={<UserOutlined />}
                style={{ background: "var(--muted)", color: "var(--ink-soft)" }}
              />
              <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>
                {username || "admin"}
              </span>
            </Button>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 0,
            background: "transparent",
            minHeight: "calc(100vh - 112px)",
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
