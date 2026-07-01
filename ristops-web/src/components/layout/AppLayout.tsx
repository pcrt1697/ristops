import { Alert, Layout, theme } from 'antd';
import { matchPath, Outlet, useLocation } from 'react-router-dom';
import AdminSidebar from './AdminSidebar.tsx';
import VenueSidebar from './VenueSidebar.tsx';
import { useGlobalError } from '../../context/error.hooks.ts';
import TopBar from './TopBar.tsx';

const { Content } = Layout;

export default function AppLayout() {
  const { error, setError } = useGlobalError();
  const { pathname } = useLocation();
  const {
    token: { colorBgContainer, colorBgLayout, borderRadiusLG },
  } = theme.useToken();
  const onClose = () => setError(null);

  // Each section owns its sidebar; mount only the one that matches the route.
  const isAdmin = pathname.startsWith('/admin');
  const venueMatch = matchPath(
    { path: '/venues/:venueId', end: false },
    pathname,
  );
  const venueId = venueMatch?.params.venueId;
  const showSidebar = isAdmin || !!venueId;

  return (
    <Layout
      style={{
        height: '100vh',
        overflow: 'hidden',
        padding: 16,
        gap: 16,
        background: colorBgLayout,
      }}
    >
      <TopBar />
      <Layout
        hasSider={showSidebar}
        style={{
          flex: 1,
          minHeight: 0,
          gap: 16,
          overflow: 'hidden',
          background: 'transparent',
        }}
      >
        {isAdmin && <AdminSidebar />}
        {venueId && <VenueSidebar venueId={venueId} />}
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
              closable={{
                closeIcon: true,
                onClose,
              }}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
