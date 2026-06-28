import { Alert, Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar.tsx';
import { useGlobalError } from '../../context/error.hooks.ts';
import TopBar from './TopBar.tsx';

const { Content } = Layout;

export default function AppLayout() {
  const { error, setError } = useGlobalError();
  const {
    token: { colorBgContainer, colorBgLayout, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden', padding: 16, gap: 16, background: colorBgLayout }}>
      <Sidebar />
      <Layout style={{ gap: 16, background: 'transparent' }}>
        <TopBar />
        <Content
          style={{
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            padding: 24,
            overflow: 'auto',
            minHeight: 0,
          }}
        >
          {error && (
            <Alert
              type="error"
              title={error}
              closable={{ onClose: () => setError(null) }}
              style={{ marginBottom: 16 }}
            />
          )}
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
