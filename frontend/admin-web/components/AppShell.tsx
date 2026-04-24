"use client";
import {
  BookOutlined,
  DashboardOutlined,
  FolderOpenOutlined,
  LogoutOutlined,
  RadarChartOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Dropdown, Layout, Menu, theme as antdTheme } from "antd";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { clearToken, getToken, api } from "@/lib/api";

const { Header, Sider, Content } = Layout;

const menuItems = [
  {
    key: "/dashboard",
    icon: <DashboardOutlined />,
    label: <Link href="/dashboard">Dashboard</Link>,
  },
  {
    key: "/books",
    icon: <BookOutlined />,
    label: <Link href="/books">图书</Link>,
  },
  {
    key: "/scanner",
    icon: <RadarChartOutlined />,
    label: <Link href="/scanner">扫描</Link>,
  },
  {
    key: "/categories",
    icon: <FolderOpenOutlined />,
    label: <Link href="/categories">分类</Link>,
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname() ?? "/books";
  const {
    token: { colorBgContainer, colorBgLayout, boxShadowTertiary, colorBorder },
  } = antdTheme.useToken();

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
    const keys = menuItems.map((m) => m.key);
    return keys.find((k) => pathname.startsWith(k)) ?? "/dashboard";
  }, [pathname]);

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
            height: 60,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontWeight: 700,
            fontSize: collapsed ? 18 : 16,
            letterSpacing: 1,
            borderBottom: "1px solid #1f2937",
          }}
        >
          {collapsed ? "📚" : "📚 Books Admin"}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          style={{ borderInlineEnd: "none", paddingTop: 8 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: colorBgContainer,
            borderBottom: `1px solid ${colorBorder}`,
            boxShadow: boxShadowTertiary,
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 16,
          }}
        >
          <Dropdown
            menu={{
              items: [
                {
                  key: "logout",
                  icon: <LogoutOutlined />,
                  label: "退出登录",
                  onClick: logout,
                },
              ],
            }}
          >
            <Button type="text" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Avatar size={28} icon={<UserOutlined />} />
              <span style={{ fontWeight: 500 }}>{username || "admin"}</span>
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
