import { Button, Card, Divider, Form, Input, Typography } from 'antd';
import { useLogin } from '../../domain/auth/auth.hooks.ts';
import type { LoginInput } from '../../domain/auth/auth.types.ts';
import { Link } from 'react-router-dom';

const { Title } = Typography;

export default function UserLoginPage() {
  const { mutate: login, isPending } = useLogin();

  const onFinish = (values: LoginInput) => {
    login(values);
  };

  return (
    <>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <Card style={{ width: 400 }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: 24 }}>
            Sign in
          </Title>
          <Form layout="vertical" onFinish={onFinish} autoComplete="off">
            <Form.Item
              label="Email"
              name="email"
              rules={[
                { required: true, message: 'Please enter your email' },
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input placeholder="you@example.com" />
            </Form.Item>
            <Form.Item
              label="Password"
              name="password"
              rules={[
                { required: true, message: 'Please enter your password' },
              ]}
            >
              <Input.Password placeholder="••••••••" />
            </Form.Item>
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={isPending}
                block
              >
                Sign in
              </Button>
            </Form.Item>
          </Form>
          <Divider plain>or</Divider>
          <div style={{ textAlign: 'center' }}>
            Don't have an account? <Link to="/register">Register</Link>
          </div>
        </Card>
      </div>
    </>
  );
}
