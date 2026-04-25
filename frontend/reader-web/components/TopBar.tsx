"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

export function TopBar() {
  const pathname = usePathname() ?? "";
  const router = useRouter();
  const navs = [
    { href: "/library", label: "书架" },
    { href: "/search", label: "搜索" },
  ];
  function logout() {
    clearToken();
    router.replace("/login");
  }
  return (
    <div className="topbar">
      <Link href="/library" className="brand" aria-label="books">
        books<span className="dot">.</span>
      </Link>
      <nav>
        {navs.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className={pathname.startsWith(n.href) ? "active" : ""}
          >
            {n.label}
          </Link>
        ))}
      </nav>
      <div className="spacer" />
      <button className="btn ghost" onClick={logout}>
        退出
      </button>
    </div>
  );
}
