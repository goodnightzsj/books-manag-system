"use client";
import { StyleProvider, createCache, extractStyle } from "@ant-design/cssinjs";
import { useServerInsertedHTML } from "next/navigation";
import { ConfigProvider } from "antd";
import type { PropsWithChildren } from "react";
import zhCN from "antd/locale/zh_CN";
import { theme } from "@/lib/theme";

export function AntdRegistry({ children }: PropsWithChildren) {
  const cache = createCache();
  useServerInsertedHTML(() => (
    <style
      id="antd"
      dangerouslySetInnerHTML={{ __html: extractStyle(cache, true) }}
    />
  ));
  return (
    <StyleProvider cache={cache} hashPriority="high">
      <ConfigProvider locale={zhCN} theme={theme}>
        {children}
      </ConfigProvider>
    </StyleProvider>
  );
}
