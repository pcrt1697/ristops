import {
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  TimePicker,
} from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import ScheduleConflictWarning from '../../components/schedule/ScheduleConflictWarning.tsx';
import {
  useConflictCandidate,
  useCreateOpeningOverride,
  useOpeningOverrideConflicts,
  useUpdateOpeningOverride,
} from '../../domain/schedule/schedule.hooks.ts';
import {
  normalizeWeekdays,
  parseTime,
  WEEKDAY_ORDER,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import {
  type SearchOpeningOverridesQuery,
  type Weekday,
} from '../../services/graphql/graphql.ts';

type Override =
  SearchOpeningOverridesQuery['serviceOpeningOverrides']['items'][number];

interface OverrideFormValues {
  dates: [Dayjs, Dayjs];
  // Single value when editing one row; multiple when bulk-creating one row per weekday.
  weekday?: Weekday | Weekday[];
  startTime: Dayjs;
  endTime: Dayjs;
  capacity: number;
  description?: string;
}

interface OverrideFormModalProps {
  serviceId: string;
  override?: Override;
  open: boolean;
  onClose: () => void;
}

export default function OverrideFormModal({
  serviceId,
  override,
  open,
  onClose,
}: OverrideFormModalProps) {
  const [form] = Form.useForm<OverrideFormValues>();
  const createOverride = useCreateOpeningOverride(serviceId);
  const updateOverride = useUpdateOpeningOverride(serviceId);
  const isEditing = !!override;
  const isPending = createOverride.isPending || updateOverride.isPending;

  const conflictCandidate = useConflictCandidate(form, override?.id);
  const conflictsQuery = useOpeningOverrideConflicts(
    serviceId,
    conflictCandidate,
  );
  const hasConflicts = (conflictsQuery.data?.length ?? 0) > 0;

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
        const startTime = values.startTime.format('HH:mm:ss');
        const endTime = values.endTime.format('HH:mm:ss');
        if (override) {
          // Editing one row: the weekday scope is immutable, not sent.
          await updateOverride.mutateAsync({
            overrideId: override.id,
            input: {
              dateStart,
              dateEnd,
              startTime,
              endTime,
              capacity: values.capacity,
              description: values.description || null,
            },
          });
        } else {
          // Creating: a multi-select produces a bulk create (one row per weekday).
          const selected = Array.isArray(values.weekday) ? values.weekday : [];
          await createOverride.mutateAsync({
            dateStart,
            dateEnd,
            weekdays: normalizeWeekdays(selected),
            startTime,
            endTime,
            capacity: values.capacity,
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
      title={isEditing ? 'Edit override' : 'Add override'}
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={isPending}
      okButtonProps={{ disabled: hasConflicts }}
      okText={isEditing ? 'Save' : 'Create'}
      destroyOnHidden
      afterOpenChange={(o) => {
        if (o) {
          form.setFieldsValue({
            dates: override
              ? [dayjs(override.dateStart), dayjs(override.dateEnd)]
              : undefined,
            weekday: override?.weekday ?? undefined,
            startTime: override ? parseTime(override.startTime) : undefined,
            endTime: override ? parseTime(override.endTime) : undefined,
            capacity: override?.capacity,
            description: override?.description ?? undefined,
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
              ? 'The weekday scope cannot be changed after creation; delete and recreate to change it.'
              : 'Select multiple to create one override per weekday. Leave empty (or select all) for every day.'
          }
        >
          <Select
            allowClear
            disabled={isEditing}
            mode={isEditing ? undefined : 'multiple'}
            placeholder="Every day"
            options={WEEKDAY_ORDER.map((w) => ({
              value: w,
              label: weekdayLabel(w),
            }))}
          />
        </Form.Item>
        <ScheduleConflictWarning
          conflicts={conflictsQuery.data}
          isLoading={conflictsQuery.isFetching}
          isError={conflictsQuery.isError}
          onRetry={() => void conflictsQuery.refetch()}
        />
        <Form.Item
          name="startTime"
          label="Opens at"
          rules={[{ required: true, message: 'Opening time is required.' }]}
        >
          <TimePicker
            format="HH:mm"
            minuteStep={5}
            needConfirm={false}
            style={{ width: '100%' }}
          />
        </Form.Item>
        <Form.Item
          name="endTime"
          label="Closes at"
          rules={[{ required: true, message: 'Closing time is required.' }]}
        >
          <TimePicker
            format="HH:mm"
            minuteStep={5}
            needConfirm={false}
            style={{ width: '100%' }}
          />
        </Form.Item>
        <Form.Item
          name="capacity"
          label="Capacity (seats)"
          rules={[
            { required: true, message: 'Capacity is required.' },
            {
              type: 'integer',
              min: 1,
              message: 'Capacity must be a whole number of at least 1.',
            },
          ]}
        >
          <InputNumber min={1} step={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="description" label="Notes">
          <Input placeholder="e.g. Ferragosto weekend" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
