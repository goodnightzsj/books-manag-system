import type { ThemeConfig } from "antd";
import {
  accent,
  fontStack,
  ink,
  paper,
  radius,
  semantic,
} from "./design-tokens";

/**
 * Ant Design theme for the Books admin console.
 *
 * Editorial archive style:
 *   - Terracotta primary (book-spine red), no indigo / violet.
 *   - Restrained radii (6 / 10), hairline rules, no glassmorphism.
 *   - Cool paper background (`#F5F4EE`) instead of blue-grey.
 *   - Sider uses deep ink, selection is the brand accent itself.
 *   - Inter / Noto Sans SC stack with `cv11` for tabular figures.
 */
export const theme: ThemeConfig = {
  cssVar: true,
  hashed: false,
  token: {
    colorPrimary: accent.base,
    colorPrimaryHover: accent.deep,
    colorPrimaryActive: accent.deep,
    colorInfo: semantic.info,
    colorSuccess: semantic.ok,
    colorWarning: semantic.warn,
    colorError: semantic.danger,
    colorLink: accent.base,
    colorLinkHover: accent.deep,

    colorBgLayout: paper.cool,
    colorBgContainer: paper.surface,
    colorBgElevated: paper.surface,
    colorBorder: paper.rule,
    colorBorderSecondary: paper.rule,

    colorText: ink.base,
    colorTextSecondary: ink.soft,
    colorTextTertiary: ink.faint,

    borderRadius: radius.md,
    borderRadiusLG: radius.lg,
    borderRadiusSM: radius.sm,

    fontFamily: fontStack.sans,
    fontSize: 14,
    fontSizeHeading1: 22,
    fontSizeHeading2: 18,
    fontSizeHeading3: 16,
    lineHeight: 1.55,

    controlHeight: 34,
    controlHeightSM: 28,
    controlHeightLG: 40,

    wireframe: false,
    motionDurationMid: "0.18s",
    motionDurationSlow: "0.24s",
  },
  components: {
    Layout: {
      headerBg: paper.surface,
      siderBg: paper.ink,
      bodyBg: paper.cool,
      triggerBg: paper.inkHover,
      headerPadding: "0 24px",
    },
    Menu: {
      darkItemBg: paper.ink,
      darkSubMenuItemBg: "#161512",
      darkItemSelectedBg: accent.base,
      darkItemSelectedColor: "#FFFFFF",
      darkItemHoverBg: paper.inkHover,
      darkItemColor: "#C9C2B0",
      itemBorderRadius: radius.md,
      itemMarginInline: 8,
    },
    Card: {
      borderRadiusLG: radius.lg,
      paddingLG: 20,
      headerBg: "transparent",
      headerFontSize: 14,
    },
    Button: {
      borderRadius: radius.md,
      defaultBorderColor: paper.rule,
      defaultColor: ink.base,
      primaryShadow: "none",
      defaultShadow: "none",
      dangerShadow: "none",
    },
    Input: {
      borderRadius: radius.md,
      activeShadow: "0 0 0 3px rgba(180, 80, 42, 0.18)",
      activeBorderColor: accent.base,
      hoverBorderColor: ink.faint,
    },
    InputNumber: {
      borderRadius: radius.md,
      activeShadow: "0 0 0 3px rgba(180, 80, 42, 0.18)",
      activeBorderColor: accent.base,
    },
    Select: {
      borderRadius: radius.md,
      optionSelectedBg: accent.soft,
      optionSelectedColor: ink.base,
    },
    Table: {
      borderRadius: radius.lg,
      headerBg: paper.muted,
      headerColor: ink.soft,
      headerSplitColor: paper.rule,
      rowHoverBg: "#F8F5EC",
      cellPaddingBlock: 12,
      cellPaddingInline: 16,
    },
    Tag: {
      borderRadiusSM: radius.sm,
      defaultBg: paper.muted,
      defaultColor: ink.soft,
    },
    Statistic: {
      titleFontSize: 12,
      contentFontSize: 26,
    },
    Form: {
      labelFontSize: 13,
      labelColor: ink.soft,
      verticalLabelPadding: "0 0 6px",
    },
    Progress: {
      remainingColor: paper.muted,
    },
    Divider: {
      colorSplit: paper.rule,
    },
    Modal: {
      borderRadiusLG: radius.lg,
      headerBg: paper.surface,
    },
    Dropdown: {
      borderRadiusLG: radius.md,
      paddingBlock: 6,
    },
    Tooltip: {
      colorBgSpotlight: paper.ink,
    },
    Breadcrumb: {
      itemColor: ink.faint,
      lastItemColor: ink.base,
      separatorColor: ink.faint,
      linkColor: ink.soft,
      linkHoverColor: accent.base,
    },
  },
};
