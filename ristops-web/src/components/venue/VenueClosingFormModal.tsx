import { DatePicker, Form, Input, Modal, Select } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import {
  useCreateVenueClosing,
  useUpdateVenueClosing,
} from '../../domain/schedule/schedule.hooks.ts';
import {
  normalizeWeekdays,
  WEEKDAY_ORDER,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import {
  type SearchVenueClosingsQuery,
  type Weekday,
} from '../../services/graphql/graphql.ts';

type VenueClosing = SearchVenueClosingsQuery['venueClosings']['items'][number];

interface VenueClosingFormValues {
  dates: [Dayjs, Dayjs];
  // Single value when editing one row; multiple when bulk-creating one row per weekday.
  weekday?: Weekday | Weekday[];
  description?: string;
}

interface VenueClosingFormModalProps {
  venueId: string;
  closing?: VenueClosing;
  open: boolean;
  onClose: () => void;
}

export default function VenueClosingFormModal({
  venueId,
  closing,
  open,
  onClose,
}: VenueClosingFormModalProps) {
  const [form] = Form.useForm<VenueClosingFormValues>();
  const createClosing = useCreateVenueClosing(venueId);
  const updateClosing = useUpdateVenueClosing(venueId);
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
        const dateStart = values.dates[0].format('YYYY-MM-DD');
        const dateEnd = values.dates[1].format('YYYY-MM-DD');
        if (closing) {
          await updateClosing.mutateAsync({
            closingId: closing.id,
            input: {
              dateStart,
              dateEnd,
              weekday: (values.weekday as Weekday | undefined) ?? null,
              description: values.description || null,
            },
          });
        } else {
          const selected = Array.isArray(values.weekday) ? values.weekday : [];
          await createClosing.mutateAsync({
            dateStart,
            dateEnd,
            weekdays: normalizeWeekdays(selected),
            description: values.description || null,
          });
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
      title={isEditing ? 'Edit venue closure' : 'Add venue closure'}
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
              ? [dayjs(closing.dateStart), dayjs(closing.dateEnd)]
              : undefined,
            weekday: closing?.weekday ?? undefined,
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
          name="weekday"
          label="Applies to"
          extra={
            isEditing
              ? 'Closes every service of the venue. Leave empty for every day in the range (e.g. select Monday to close every Monday).'
              : 'Closes every service of the venue. Select multiple to create one closure per weekday. Leave empty (or select all) to close every day.'
          }
        >
          <Select
            allowClear
            mode={isEditing ? undefined : 'multiple'}
            placeholder="Every day"
            options={WEEKDAY_ORDER.map((w) => ({
              value: w,
              label: weekdayLabel(w),
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
