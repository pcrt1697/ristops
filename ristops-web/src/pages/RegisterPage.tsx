import { Button, Card, Form, Input, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { useRegister } from '../domain/auth/auth.hooks.ts';
import type { RegisterInput } from '../domain/auth/auth.types.ts';

const { Title } = Typography;

interface RegisterFormValues extends RegisterInput {
  confirmPassword: string;
}

export default function RegisterPage() {
  const { mutate: register, isPending } = useRegister();

  const onFinish = (values: RegisterFormValues) => {
    register({
      username: values.username,
      displayName: values.displayName,
      email: values.email,
      password: values.password,
    });
  };

  return (
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
          Register
        </Title>
        <Form layout="vertical" onFinish={onFinish} autoComplete="off">
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, message: 'Please enter a username' }]}
          >
            <Input placeholder="john42" />
          </Form.Item>
          <Form.Item
            label="Display name"
            name="displayName"
            rules={[{ required: true, message: 'Please enter a display name' }]}
          >
            <Input placeholder="John" />
          </Form.Item>
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
            rules={[{ required: true, message: 'Please enter a password' }]}
          >
            <Input.Password placeholder="••••••••" />
          </Form.Item>
          <Form.Item
            label="Confirm password"
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm your password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="••••••••" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isPending} block>
              Register
            </Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            Already have an account? <Link to="/login">Sign in</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
