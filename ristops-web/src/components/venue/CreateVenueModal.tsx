import { Form, Input, Modal } from 'antd';
import { useCreateVenue } from '../../domain/venue/venue.hooks.ts';

interface CreateVenueFormValues {
  name: string;
  address: string;
  description?: string;
}

interface CreateVenueModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CreateVenueModal({ open, onClose }: CreateVenueModalProps) {
  const [form] = Form.useForm<CreateVenueFormValues>();
  const createVenue = useCreateVenue();

  function handleCancel() {
    form.resetFields();
    onClose();
  }

  function handleSubmit() {
    form
      .validateFields()
      .then(async (values) => {
        // The mutation rejects on error, so the modal stays open and the
        // hook surfaces the failure; we only reset/close on success.
        await createVenue.mutateAsync(values);
        form.resetFields();
        onClose();
      })
      .catch(() => {
        // validation and mutation errors are handled inline / by the hook
      });
  }

  return (
    <Modal
      title="Create venue"
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={createVenue.isPending}
      okText="Create"
      style={{ maxWidth: '90vw' }}
      styles={{
        mask: { backdropFilter: 'blur(4px)' },
        container: { maxHeight: '90vh', display: 'flex', flexDirection: 'column' },
        header: { textAlign: 'center' },
        body: { flex: 1, overflowY: 'auto', paddingTop: 24 },
      }}
    >
      <Form form={form} layout="vertical" style={{ maxWidth: 600, margin: '0 auto' }}>
        <Form.Item
          name="name"
          label="Name"
          rules={[
            { required: true, message: 'Name is required.' },
            { max: 120, message: 'Name must be at most 120 characters.' },
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="address"
          label="Address"
          rules={[
            { required: true, message: 'Address is required.' },
            { max: 255, message: 'Address must be at most 255 characters.' },
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="description"
          label="Description"
          rules={[
            { max: 1000, message: 'Description must be at most 1000 characters.' },
          ]}
        >
          <Input.TextArea rows={4} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
