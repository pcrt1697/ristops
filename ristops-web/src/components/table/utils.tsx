import { FrownOutlined } from '@ant-design/icons';

export function renderAccessDeniedTableContent() {
  return (
    <div style={{ textAlign: 'center' }}>
      <FrownOutlined style={{ fontSize: 20 }} />
      <p>You cannot access this content</p>
    </div>
  );
}
