import { Button, Card, Form, Input, Typography } from 'antd';
import { useAuth, useUpdateMe } from '../domain/auth/auth.hooks.ts';

const { Title } = Typography;

interface ProfileFormValues {
  username: string;
  displayName: string;
  email: string;
  password: string;
}

export default function UserProfilePage() {
  const { user } = useAuth();
  const { mutate: updateMe, isPending } = useUpdateMe();

  const onFinish = (values: ProfileFormValues) => {
    updateMe({
      input: {
        username: values.username || undefined,
        displayName: values.displayName || undefined,
        email: values.email || undefined,
        password: values.password || undefined,
      },
    });
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}>
      <Card style={{ width: 500 }}>
        <Title level={3} style={{ marginBottom: 24 }}>
          Profile
        </Title>
        <Form
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            username: user?.username,
            displayName: user?.displayName,
            email: user?.email,
          }}
        >
          <Form.Item label="Username" name="username">
            <Input />
          </Form.Item>
          <Form.Item label="Display name" name="displayName">
            <Input />
          </Form.Item>
          <Form.Item label="Email" name="email">
            <Input />
          </Form.Item>
          <Form.Item label="New password" name="password">
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isPending} block>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
