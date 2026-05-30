import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import TopBar from './TopBar.tsx';

const { Content } = Layout;

export default function AppLayout() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <TopBar />
      <Content>
        <Outlet />
      </Content>
    </Layout>
  );
}
