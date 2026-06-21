import { useState } from 'react';
import {
  Button,
  Descriptions,
  Divider,
  Form,
  Input,
  Modal,
  Space,
  theme,
} from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useAuth, useUpdateMe } from '../../domain/auth/auth.hooks.ts';
import type { ProfileFormValues } from '../../domain/auth/auth.types.ts';

const { useToken } = theme;

export default function UserProfilePage() {
  const { token } = useToken();
  const { user } = useAuth();
  const { mutate: updateMe, isPending } = useUpdateMe();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<ProfileFormValues>();

  const handleOpen = () => {
    form.setFieldsValue({
      username: user?.username,
      displayName: user?.displayName ?? undefined,
      email: user?.email,
      password: undefined,
    });
    setOpen(true);
  };

  const handleClose = () => {
    form.resetFields();
    setOpen(false);
  };

  const onFinish = (values: ProfileFormValues) => {
    updateMe(
      {
        username: values.username || undefined,
        displayName: values.displayName || undefined,
        email: values.email || undefined,
        password: values.password || undefined,
      },
      { onSuccess: handleClose },
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          padding: 24,
          background: token.colorBgContainer,
          borderRadius: token.borderRadiusLG,
          minHeight: 280,
        }}
      >
        <Divider titlePlacement="start">
          <Space>
            Profile
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={handleOpen}
            />
          </Space>
        </Divider>

        <Descriptions column={1}>
          <Descriptions.Item label="Username">
            {user?.username}
          </Descriptions.Item>
          <Descriptions.Item label="Display name">
            {user?.displayName ?? '—'}
          </Descriptions.Item>
          <Descriptions.Item label="Email">{user?.email}</Descriptions.Item>
          <Descriptions.Item label="Member since">
            {user?.createdAt
              ? new Date(user.createdAt).toLocaleDateString()
              : '—'}
          </Descriptions.Item>
        </Descriptions>
      </div>

      <Modal
        title="Edit profile"
        open={open}
        onCancel={handleClose}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 16 }}
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
          <Form.Item
            label="New password"
            name="password"
            extra="Leave blank to keep your current password."
          >
            <Input.Password />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Button onClick={handleClose} style={{ marginRight: 8 }}>
              Cancel
            </Button>
            <Button type="primary" htmlType="submit" loading={isPending}>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
