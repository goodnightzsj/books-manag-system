import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AntdRegistry } from "@/components/AntdRegistry";
import "./globals.css";

export const metadata: Metadata = {
  title: "Books Admin",
  description: "Books Management System -- admin console",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  );
}
