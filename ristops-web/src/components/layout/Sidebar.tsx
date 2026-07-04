import { useState } from 'react';
import { Button, Layout, Menu, type MenuProps, theme } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';

const { Sider } = Layout;

interface SidebarProps {
  items: MenuProps['items'];
}

/** Collect the keys of all items, recursing into group/submenu children. */
function collectKeys(items: MenuProps['items']): string[] {
  const keys: string[] = [];
  for (const item of items ?? []) {
    if (!item) continue;
    if (typeof item.key === 'string') keys.push(item.key);
    if ('children' in item && item.children)
      keys.push(...collectKeys(item.children));
  }
  return keys;
}

/** Presentational sidebar shell: renders the given menu items with a collapse toggle. */
export default function Sidebar({ items }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { token } = theme.useToken();

  // Highlight the most specific (longest) item path that prefixes the location.
  const selectedKey = collectKeys(items)
    .filter((key) => location.pathname.startsWith(key))
    .sort((a, b) => b.length - a.length)[0];

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      collapsedWidth={60}
      trigger={null}
      theme="light"
      style={{
        height: '100%',
        overflow: 'hidden',
        borderRadius: token.borderRadiusLG,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Menu
          mode="inline"
          selectedKeys={selectedKey ? [selectedKey] : []}
          items={items}
          style={{
            flex: 1,
            overflow: 'auto',
            borderInlineEnd: 0,
            paddingTop: 8,
          }}
        />
        <Button
          type="text"
          block
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setCollapsed(!collapsed)}
          style={{
            height: 48,
            borderTop: `1px solid ${token.colorSplit}`,
            borderRadius: 0,
          }}
        />
      </div>
    </Sider>
  );
}
