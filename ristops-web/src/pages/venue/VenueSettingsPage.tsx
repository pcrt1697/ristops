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
  Tag,
  theme,
  Typography,
} from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import {
  useActivateVenue,
  useCloseVenue,
  useDisableVenue,
  useEnableVenue,
  useUpdateVenue,
  useVenue,
} from '../../domain/venue/venue.hooks.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { statusTagColor } from '../../domain/venue/venue.utils.ts';
import { ResourceType, VenueStatus } from '../../services/graphql/graphql.ts';

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
  const { isAllowed: canActivate } = useCan(resource, 'venue:activate');
  const { isAllowed: canClose } = useCan(resource, 'venue:close');
  const { isAllowed: canDisable } = useCan(resource, 'venue:disable');
  const { isAllowed: canEnable } = useCan(resource, 'venue:enable');

  const { mutate: updateVenue, isPending: isUpdating } = useUpdateVenue(venueId);
  const { mutate: activateVenue, isPending: isActivating } = useActivateVenue();
  const { mutate: closeVenue, isPending: isClosing } = useCloseVenue();
  const { mutate: disableVenue, isPending: isDisabling } = useDisableVenue();
  const { mutate: enableVenue, isPending: isEnabling } = useEnableVenue();

  const [editOpen, setEditOpen] = useState(false);
  const [closeOpen, setCloseOpen] = useState(false);
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

  const closeCloseModal = () => {
    setConfirmName('');
    setCloseOpen(false);
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

      {(canActivate || canClose || canDisable || canEnable) && (
        <>
          <Divider titlePlacement="start" style={{ marginTop: 48 }}>
            Status
          </Divider>
          <Card
            styles={{
              body: {
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                flexWrap: 'wrap',
              },
            }}
            style={{
              borderColor:
                venue.status === VenueStatus.Disabled ? token.colorError : undefined,
            }}
          >
            <div style={{ flex: 1 }}>
              <Text strong>Manage venue status</Text>
              <br />
              <Text type="secondary">
                Activate, close, disable, or re-enable this venue depending on its
                current status.
              </Text>
            </div>
            <Space>
              {canActivate &&
                (venue.status === VenueStatus.Pending ||
                  venue.status === VenueStatus.Closed) && (
                  <Button
                    type="primary"
                    loading={isActivating}
                    onClick={() => activateVenue(venueId)}
                  >
                    {venue.status === VenueStatus.Closed ? 'Reopen' : 'Activate'}
                  </Button>
                )}
              {canClose && venue.status === VenueStatus.Active && (
                <Button danger onClick={() => setCloseOpen(true)}>
                  Close venue
                </Button>
              )}
              {canDisable &&
                (venue.status === VenueStatus.Pending ||
                  venue.status === VenueStatus.Active) && (
                  <Button
                    danger
                    loading={isDisabling}
                    onClick={() => disableVenue(venueId)}
                  >
                    Disable
                  </Button>
                )}
              {canEnable && venue.status === VenueStatus.Disabled && (
                <Button
                  type="primary"
                  loading={isEnabling}
                  onClick={() => enableVenue(venueId)}
                >
                  Enable
                </Button>
              )}
            </Space>
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
        title="Close venue"
        open={closeOpen}
        onCancel={closeCloseModal}
        okText="Close venue"
        okButtonProps={{
          danger: true,
          disabled: confirmName !== venue.name,
          loading: isClosing,
        }}
        onOk={() => closeVenue(venueId)}
      >
        <Text>
          The venue will stop accepting new activity. Nothing is deleted — reopen
          it any time from this page. Type <Text strong>{venue.name}</Text> to
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
