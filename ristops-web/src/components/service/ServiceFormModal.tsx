import { DatePicker, Form, Input, InputNumber, Modal } from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
import {
  useCreateService,
  useUpdateService,
} from '../../domain/service/service.hooks.ts';
import type { ListServicesQuery } from '../../services/graphql/graphql.ts';

type ServiceListItem = ListServicesQuery['listServices'][number];

interface ServiceFormValues {
  name: string;
  description?: string;
  dateFrom: Dayjs;
  dateTo?: Dayjs | null;
  capacity: number;
}

interface ServiceFormModalProps {
  venueId: string;
  service?: ServiceListItem;
  open: boolean;
  onClose: () => void;
}

/**
 * Create or edit a service: what it is, when it runs, and how many seats it takes. Its hours are
 * set separately on the schedule page — a service with no openings simply never runs.
 *
 * The end date is optional: left empty the service runs indefinitely, and setting it equal to the
 * start date makes a one-shot service for a single date.
 */
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
        const input = {
          name: values.name,
          description: values.description ?? null,
          dateFrom: values.dateFrom.format('YYYY-MM-DD'),
          dateTo: values.dateTo ? values.dateTo.format('YYYY-MM-DD') : null,
          capacity: values.capacity,
        };
        if (service) {
          await updateService.mutateAsync({ id: service.id, input });
        } else {
          await createService.mutateAsync({ ...input, venueId });
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
      afterOpenChange={(o) => {
        if (o) {
          form.setFieldsValue({
            name: service?.name,
            description: service?.description ?? undefined,
            dateFrom: service ? dayjs(service.dateFrom) : dayjs(),
            dateTo: service?.dateTo ? dayjs(service.dateTo) : null,
            capacity: service?.capacity,
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
          name="dateFrom"
          label="Runs from"
          extra="First date this service is offered."
          rules={[{ required: true, message: 'A start date is required.' }]}
        >
          <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
        </Form.Item>
        <Form.Item
          name="dateTo"
          label="Runs until"
          extra="Leave empty to run indefinitely, or match the start date for a one-off."
          dependencies={['dateFrom']}
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value: Dayjs | null | undefined) {
                const from = getFieldValue('dateFrom') as Dayjs | undefined;
                if (!value || !from || !value.isBefore(from, 'day')) {
                  return Promise.resolve();
                }
                return Promise.reject(
                  new Error('The end date must not be before the start date.'),
                );
              },
            }),
          ]}
        >
          <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" allowClear />
        </Form.Item>
        <Form.Item
          name="capacity"
          label="Capacity (seats)"
          extra="How many seats this service can take on any date it runs."
          rules={[
            { required: true, message: 'Capacity is required.' },
            {
              type: 'integer',
              min: 1,
              message: 'Capacity must be a whole number of seats (at least 1).',
            },
          ]}
        >
          <InputNumber min={1} step={1} placeholder="e.g. 40" style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
