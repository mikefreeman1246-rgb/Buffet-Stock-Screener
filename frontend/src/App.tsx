import { ConfigProvider, Layout, Tabs, theme } from "antd";
import AppHeader from "./components/Header";
import ScreenerView from "./components/ScreenerView";
import Weathercast from "./components/market/Weathercast";
import { ScreenerContext } from "./components/ScreenerContext";
import { useScreenerController } from "./hooks/useScreenerController";

const { Content } = Layout;

const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#2dd4bf",
    colorBgBase: "#0b0e14",
    colorBgContainer: "#111520",
    colorBgElevated: "#161b28",
    colorBgLayout: "#0b0e14",
    colorBorder: "rgba(255, 255, 255, 0.10)",
    colorBorderSecondary: "rgba(255, 255, 255, 0.06)",
    colorText: "#e8eaed",
    colorTextSecondary: "#8b919e",
    colorTextTertiary: "#5c6370",
    colorSuccess: "#34d399",
    colorError: "#f87171",
    colorWarning: "#fbbf24",
    colorInfo: "#60a5fa",
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif",
    fontSize: 13,
    borderRadius: 6,
    borderRadiusSM: 4,
    borderRadiusLG: 8,
    controlHeight: 32,
    controlHeightSM: 26,
  },
  components: {
    Layout: { headerBg: "#0d1117", headerHeight: 52, headerPadding: "0 20px", bodyBg: "#0b0e14" },
    Table: {
      headerBg: "#111520", headerColor: "#5c6370", rowHoverBg: "#1c2235",
      borderColor: "rgba(255, 255, 255, 0.06)", cellPaddingBlockSM: 8, cellPaddingInlineSM: 10,
    },
    Tabs: { itemColor: "#5c6370", itemActiveColor: "#2dd4bf", itemSelectedColor: "#2dd4bf", inkBarColor: "#2dd4bf" },
    Slider: {
      trackBg: "#2dd4bf", trackHoverBg: "#5eead4", handleColor: "#2dd4bf",
      handleActiveColor: "#5eead4", railBg: "rgba(255,255,255,0.10)",
    },
    Button: { primaryColor: "#0b0e14", fontWeight: 500 },
  },
};

export default function App() {
  // One screener controller instance, shared by the layout header (via context)
  // and the ScreenerView tab. Lives here because the header sits in Layout.Header,
  // outside the tabbed <Content>.
  const controller = useScreenerController();

  return (
    <ConfigProvider theme={darkTheme}>
      <ScreenerContext.Provider value={controller}>
        <Layout style={{ minHeight: "100vh" }}>
          <Layout.Header
            style={{ display: "flex", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.08)" }}
          >
            <AppHeader
              stats={controller.stats}
              assumptions={controller.assumptions}
              onOpenAssumptions={() => controller.setDrawerOpen(true)}
              onPullDone={controller.handlePullDone}
            />
          </Layout.Header>
          <Content style={{ padding: "16px 20px 28px" }}>
            <Tabs
              defaultActiveKey="screener"
              items={[
                { key: "screener", label: "Value Screener", children: <ScreenerView /> },
                { key: "weather", label: "Market Weathercast", children: <Weathercast /> },
              ]}
            />
          </Content>
        </Layout>
      </ScreenerContext.Provider>
    </ConfigProvider>
  );
}
