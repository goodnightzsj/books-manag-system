"use client";
import { StyleProvider, createCache, extractStyle } from "@ant-design/cssinjs";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { useServerInsertedHTML } from "next/navigation";
import { useMemo, useRef, type PropsWithChildren } from "react";

import { theme } from "@/lib/theme";

/**
 * Ant Design 5 + Next.js App Router style registry.
 *
 * Two upstream-mandated details that the simpler version skipped:
 *   1. cache MUST be memoised. A fresh `createCache()` per render makes
 *      the SSR-emitted CSS hash drift from the CSR one and antd Form
 *      crashes during hydration with the classic
 *        TypeError: Cannot read properties of null (reading '1')
 *   2. `useServerInsertedHTML` callback fires on every render; an
 *      `inserted` ref keeps the <style> tag emitted exactly once.
 */
export function AntdRegistry({ children }: PropsWithChildren) {
  const cache = useMemo(() => createCache(), []);
  const inserted = useRef(false);

  useServerInsertedHTML(() => {
    if (inserted.current) return null;
    inserted.current = true;
    return (
      <style
        id="antd"
        dangerouslySetInnerHTML={{ __html: extractStyle(cache, true) }}
      />
    );
  });

  return (
    <StyleProvider cache={cache} hashPriority="high">
      <ConfigProvider locale={zhCN} theme={theme}>
        {children}
      </ConfigProvider>
    </StyleProvider>
  );
}
