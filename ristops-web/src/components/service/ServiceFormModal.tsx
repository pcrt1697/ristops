import { Form, Input, InputNumber, Modal } from 'antd';
import {
  useCreateService,
  useUpdateService,
} from '../../domain/service/service.hooks.ts';
import type { ListServicesQuery } from '../../services/graphql/graphql.ts';

type ServiceListItem = ListServicesQuery['listServices'][number];

interface ServiceFormValues {
  name: string;
  description?: string;
  turnTimeM: number;
  slotIntervalM: number;
  advanceNoticeM: number;
  gracePeriodM: number;
}

interface ServiceFormModalProps {
  venueId: string;
  service?: ServiceListItem;
  open: boolean;
  onClose: () => void;
}

export default function ServiceFormModal({
  venueId,
  service,
  open,
  onClose,
}: ServiceFormModalProps) {
  const [form] = Form.useForm<ServiceFormValues>();
  const createService = useCreateService(venueId);
  const updateService = useUpdateService(venueId);
  const isEditing = !!service;
  const isPending = createService.isPending || updateService.isPending;

  function handleCancel() {
    form.resetFields();
    onClose();
  }

  function handleSubmit() {
    form
      .validateFields()
      .then(async (values) => {
        if (service) {
          await updateService.mutateAsync({ id: service.id, input: values });
        } else {
          await createService.mutateAsync({ ...values, venueId });
        }
        form.resetFields();
        onClose();
      })
      .catch(() => {
        // validation and mutation errors are handled inline / by the hook
      });
  }

  return (
    <Modal
      title={isEditing ? 'Edit service' : 'Add service'}
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={isPending}
      okText={isEditing ? 'Save' : 'Create'}
      destroyOnHidden
      centered
      styles={{
        container: { height: '80dvh', display: 'flex', flexDirection: 'column' },
        body: { flex: 1, overflowY: 'auto' },
      }}
      afterOpenChange={(o) => {
        if (o) {
          form.setFieldsValue({
            name: service?.name,
            description: service?.description ?? undefined,
            turnTimeM: service?.turnTimeM,
            slotIntervalM: service?.slotIntervalM,
            advanceNoticeM: service?.advanceNoticeM,
            gracePeriodM: service?.gracePeriodM,
          });
        }
      }}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="name"
          label="Name"
          rules={[
            { required: true, message: 'Name is required.' },
            { max: 120, message: 'Name must be at most 120 characters.' },
          ]}
        >
          <Input placeholder="e.g. Lunch" />
        </Form.Item>
        <Form.Item
          name="description"
          label="Description"
          rules={[
            { max: 1000, message: 'Description must be at most 1000 characters.' },
          ]}
        >
          <Input.TextArea rows={3} placeholder="e.g. Weekday lunch service" />
        </Form.Item>
        <Form.Item
          name="turnTimeM"
          label="Turn time (minutes)"
          extra="How long a table is held for a single reservation."
          rules={[
            { required: true, message: 'Turn time is required.' },
            {
              type: 'integer',
              min: 1,
              message: 'Turn time must be a whole number of minutes (at least 1).',
            },
          ]}
        >
          <InputNumber min={1} step={1} placeholder="e.g. 60" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="slotIntervalM"
          label="Slot interval (minutes)"
          extra="Spacing between consecutive bookable time slots."
          rules={[
            { required: true, message: 'Slot interval is required.' },
            {
              type: 'integer',
              min: 1,
              message:
                'Slot interval must be a whole number of minutes (at least 1).',
            },
          ]}
        >
          <InputNumber min={1} step={1} placeholder="e.g. 15" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="advanceNoticeM"
          label="Minimum notice (minutes)"
          extra="How far ahead a guest must book before a slot's start time."
          rules={[
            { required: true, message: 'Minimum notice is required.' },
            {
              type: 'integer',
              min: 1,
              message:
                'Minimum notice must be a whole number of minutes (at least 1).',
            },
          ]}
        >
          <InputNumber min={1} step={1} placeholder="e.g. 120" style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="gracePeriodM"
          label="Grace period (minutes)"
          extra="Delay past the start time before a reservation can be marked a no-show."
          rules={[
            { required: true, message: 'Grace period is required.' },
            {
              type: 'integer',
              min: 0,
              message:
                'Grace period must be a whole number of minutes (0 or more).',
            },
          ]}
        >
          <InputNumber min={0} step={1} placeholder="e.g. 15" style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
