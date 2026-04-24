import type { ThemeConfig } from "antd";

/**
 * Custom Ant Design token set for the Books admin console.
 * Tuned for dense data screens: tighter radius, slightly cooler primary.
 */
export const theme: ThemeConfig = {
  cssVar: true,
  hashed: false,
  token: {
    colorPrimary: "#4F46E5",
    colorInfo: "#4F46E5",
    colorSuccess: "#10B981",
    colorWarning: "#F59E0B",
    colorError: "#EF4444",
    colorBgLayout: "#F6F7FB",
    colorBgContainer: "#FFFFFF",
    colorBorderSecondary: "#E6E8F0",
    borderRadius: 10,
    borderRadiusLG: 14,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Noto Sans SC', sans-serif",
    fontSize: 14,
    controlHeight: 36,
    wireframe: false,
  },
  components: {
    Layout: {
      headerBg: "#FFFFFF",
      siderBg: "#111827",
      bodyBg: "#F6F7FB",
      triggerBg: "#1F2937",
      headerPadding: "0 24px",
    },
    Menu: {
      darkItemBg: "#111827",
      darkSubMenuItemBg: "#0B1220",
      darkItemSelectedBg: "#4338CA",
      darkItemHoverBg: "#1F2937",
      itemBorderRadius: 8,
    },
    Card: {
      borderRadiusLG: 14,
      paddingLG: 20,
    },
    Button: {
      borderRadius: 8,
    },
    Table: {
      borderRadius: 12,
      headerBg: "#F1F3F9",
      headerColor: "#374151",
    },
    Input: {
      borderRadius: 8,
    },
    Tag: {
      borderRadiusSM: 6,
    },
  },
};
