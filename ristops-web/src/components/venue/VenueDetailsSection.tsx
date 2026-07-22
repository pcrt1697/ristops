import { useState } from 'react';
import {
  Button,
  Descriptions,
  Divider,
  Form,
  Input,
  Modal,
  Space,
  Tag,
} from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useUpdateVenue } from '../../domain/venue/venue.hooks.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { statusTagColor } from '../../domain/venue/venue.utils.ts';
import {
  type GetVenueQuery,
  ResourceType,
} from '../../services/graphql/graphql.ts';

interface VenueFormValues {
  name: string;
  address: string;
  description?: string;
}

interface VenueDetailsSectionProps {
  venue: GetVenueQuery['venue'];
}

export default function VenueDetailsSection({
  venue,
}: VenueDetailsSectionProps) {
  const { isAllowed: canEdit } = useCan(
    { type: ResourceType.Venue, id: venue.id },
    'venue:edit',
  );
  const { mutate: updateVenue, isPending: isUpdating } = useUpdateVenue(
    venue.id,
  );

  const [editOpen, setEditOpen] = useState(false);
  const [form] = Form.useForm<VenueFormValues>();

  const openEdit = () => {
    form.setFieldsValue({
      name: venue.name,
      address: venue.address,
      description: venue.description ?? undefined,
    });
    setEditOpen(true);
  };

  const closeEdit = () => {
    form.resetFields();
    setEditOpen(false);
  };

  const onFinish = (values: VenueFormValues) => {
    updateVenue(
      {
        name: values.name || undefined,
        address: values.address || undefined,
        description: values.description || undefined,
      },
      { onSuccess: closeEdit },
    );
  };

  return (
    <>
      <Divider titlePlacement="start">
        <Space>
          Venue
          {canEdit && (
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={openEdit}
            />
          )}
        </Space>
      </Divider>

      <Descriptions column={1}>
        <Descriptions.Item label="Name">{venue.name}</Descriptions.Item>
        <Descriptions.Item label="Address">{venue.address}</Descriptions.Item>
        <Descriptions.Item label="Description">
          {venue.description ?? '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Status">
          <Tag color={statusTagColor[venue.status]}>{venue.status}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Created">
          {new Date(venue.createdAt).toLocaleDateString()}
        </Descriptions.Item>
      </Descriptions>

      <Modal
        title="Edit venue"
        open={editOpen}
        onCancel={closeEdit}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            label="Name"
            name="name"
            rules={[{ required: true, message: 'Name is required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Address"
            name="address"
            rules={[{ required: true, message: 'Address is required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Button onClick={closeEdit} style={{ marginRight: 8 }}>
              Cancel
            </Button>
            <Button type="primary" htmlType="submit" loading={isUpdating}>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
