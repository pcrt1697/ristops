import { DatePicker, Form, Input, Modal, Select } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import {
  useCreateClosing,
  useUpdateClosing,
} from '../../domain/schedule/schedule.hooks.ts';
import { useListVenueServices } from '../../domain/service/service.hooks.ts';
import type { SearchClosingsQuery } from '../../services/graphql/graphql.ts';

type Closing = SearchClosingsQuery['venueClosings']['items'][number];

interface ClosingFormValues {
  dates: [Dayjs, Dayjs];
  serviceIds: string[];
  description?: string;
}

interface ClosingFormModalProps {
  venueId: string;
  closing?: Closing;
  open: boolean;
  onClose: () => void;
}

/**
 * Create or edit a closure: a date range and the services it takes off the calendar. Selecting
 * every service is how a venue-wide shutdown is expressed.
 *
 * A closure is also what makes room for a one-off service on a date the regular one already
 * covers — which is why shrinking or deleting one can be refused by the backend when it would
 * leave two services open at the same time.
 */
export default function ClosingFormModal({
  venueId,
  closing,
  open,
  onClose,
}: ClosingFormModalProps) {
  const [form] = Form.useForm<ClosingFormValues>();
  const createClosing = useCreateClosing(venueId);
  const updateClosing = useUpdateClosing(venueId);
  const { data: services } = useListVenueServices(venueId);
  const isEditing = !!closing;
  const isPending = createClosing.isPending || updateClosing.isPending;

  function handleCancel() {
    form.resetFields();
    onClose();
  }

  function handleSubmit() {
    form
      .validateFields()
      .then(async (values) => {
        const input = {
          dateFrom: values.dates[0].format('YYYY-MM-DD'),
          dateTo: values.dates[1].format('YYYY-MM-DD'),
          serviceIds: values.serviceIds,
          description: values.description || null,
        };
        if (closing) {
          await updateClosing.mutateAsync({ id: closing.id, input });
        } else {
          await createClosing.mutateAsync(input);
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
      title={isEditing ? 'Edit closure' : 'Add closure'}
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={isPending}
      okText={isEditing ? 'Save' : 'Create'}
      destroyOnHidden
      afterOpenChange={(o) => {
        if (o) {
          form.setFieldsValue({
            dates: closing
              ? [dayjs(closing.dateFrom), dayjs(closing.dateTo)]
              : undefined,
            serviceIds: closing?.serviceIds ?? [],
            description: closing?.description ?? undefined,
          });
        }
      }}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="dates"
          label="Dates"
          rules={[{ required: true, message: 'A date range is required.' }]}
        >
          <DatePicker.RangePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="serviceIds"
          label="Closes"
          extra="Select every service to close the venue entirely for these dates."
          rules={[{ required: true, message: 'Pick at least one service.' }]}
        >
          <Select
            mode="multiple"
            placeholder="Pick the services to close"
            options={(services?.listServices ?? []).map((service) => ({
              value: service.id,
              label: service.name,
            }))}
          />
        </Form.Item>
        <Form.Item name="description" label="Notes">
          <Input placeholder="e.g. Winter break" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
