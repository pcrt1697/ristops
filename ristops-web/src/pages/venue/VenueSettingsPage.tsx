import { useState } from 'react';
import {
  Button,
  Card,
  Descriptions,
  Divider,
  Form,
  Input,
  Modal,
  Space,
  Spin,
  theme,
  Typography,
} from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import {
  useDeleteVenue,
  useUpdateVenue,
  useVenue,
} from '../../domain/venue/venue.hooks.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';

const { Text } = Typography;

interface VenueFormValues {
  name: string;
  address: string;
  description?: string;
}

export default function VenueSettingsPage() {
  const { venueId = '' } = useParams<{ venueId: string }>();
  const { token } = theme.useToken();
  const { data, isLoading } = useVenue(venueId);
  const venue = data?.venue;

  const resource = { type: ResourceType.Venue, id: venueId };
  const { isAllowed: canEdit } = useCan(resource, 'venue:edit');
  const { isAllowed: canDelete } = useCan(resource, 'venue:remove');

  const { mutate: updateVenue, isPending: isUpdating } = useUpdateVenue(venueId);
  const { mutate: deleteVenue, isPending: isDeleting } = useDeleteVenue();

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [confirmName, setConfirmName] = useState('');
  const [form] = Form.useForm<VenueFormValues>();

  if (isLoading) return <Spin />;
  if (!venue) return null;

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

  const closeDelete = () => {
    setConfirmName('');
    setDeleteOpen(false);
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
        <Descriptions.Item label="Created">
          {new Date(venue.createdAt).toLocaleDateString()}
        </Descriptions.Item>
      </Descriptions>

      {canDelete && (
        <>
          <Divider titlePlacement="start" style={{ marginTop: 48 }}>
            <Text type="danger">Danger zone</Text>
          </Divider>
          <Card
            styles={{ body: { display: 'flex', alignItems: 'center', gap: 16 } }}
            style={{ borderColor: token.colorError }}
          >
            <div style={{ flex: 1 }}>
              <Text strong>Delete this venue</Text>
              <br />
              <Text type="secondary">
                Once deleted, the venue and its access grants are gone. This
                cannot be undone.
              </Text>
            </div>
            <Button danger onClick={() => setDeleteOpen(true)}>
              Delete venue
            </Button>
          </Card>
        </>
      )}

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

      <Modal
        title="Delete venue"
        open={deleteOpen}
        onCancel={closeDelete}
        okText="Delete venue"
        okButtonProps={{
          danger: true,
          disabled: confirmName !== venue.name,
          loading: isDeleting,
        }}
        onOk={() => deleteVenue(venueId)}
      >
        <Text>
          This action cannot be undone. Type <Text strong>{venue.name}</Text> to
          confirm.
        </Text>
        <Input
          value={confirmName}
          onChange={(e) => setConfirmName(e.target.value)}
          placeholder={venue.name}
          style={{ marginTop: 12 }}
        />
      </Modal>
    </>
  );
}
