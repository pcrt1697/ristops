import { DatePicker, Form, Input, InputNumber, Modal, Select } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import ScheduleConflictWarning from '../../components/schedule/ScheduleConflictWarning.tsx';
import {
  useCapacityOverrideConflicts,
  useConflictCandidate,
  useCreateCapacityOverride,
  useUpdateCapacityOverride,
} from '../../domain/schedule/schedule.hooks.ts';
import {
  normalizeWeekdays,
  WEEKDAY_ORDER,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import {
  type SearchCapacityOverridesQuery,
  type Weekday,
} from '../../services/graphql/graphql.ts';

type CapacityOverride =
  SearchCapacityOverridesQuery['serviceCapacityOverrides']['items'][number];

interface CapacityFormValues {
  dates: [Dayjs, Dayjs];
  // Single value when editing one row; multiple when bulk-creating one row per weekday.
  weekday?: Weekday | Weekday[];
  capacityDelta: number;
  description?: string;
}

interface CapacityFormModalProps {
  serviceId: string;
  capacityOverride?: CapacityOverride;
  open: boolean;
  onClose: () => void;
}

export default function CapacityFormModal({
  serviceId,
  capacityOverride,
  open,
  onClose,
}: CapacityFormModalProps) {
  const [form] = Form.useForm<CapacityFormValues>();
  const createOverride = useCreateCapacityOverride(serviceId);
  const updateOverride = useUpdateCapacityOverride(serviceId);
  const isEditing = !!capacityOverride;
  const isPending = createOverride.isPending || updateOverride.isPending;

  const conflictCandidate = useConflictCandidate(form, capacityOverride?.id);
  const conflictsQuery = useCapacityOverrideConflicts(
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
        if (capacityOverride) {
          // Editing one row: the weekday scope is immutable, not sent.
          await updateOverride.mutateAsync({
            capacityOverrideId: capacityOverride.id,
            input: {
              dateStart,
              dateEnd,
              capacityDelta: values.capacityDelta,
              description: values.description || null,
            },
          });
        } else {
          const selected = Array.isArray(values.weekday) ? values.weekday : [];
          await createOverride.mutateAsync({
            dateStart,
            dateEnd,
            weekdays: normalizeWeekdays(selected),
            capacityDelta: values.capacityDelta,
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
      title={isEditing ? 'Edit capacity change' : 'Add capacity change'}
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
            dates: capacityOverride
              ? [
                  dayjs(capacityOverride.dateStart),
                  dayjs(capacityOverride.dateEnd),
                ]
              : undefined,
            weekday: capacityOverride?.weekday ?? undefined,
            capacityDelta: capacityOverride?.capacityDelta,
            description: capacityOverride?.description ?? undefined,
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
              : 'Select multiple to create one capacity change per weekday. Leave empty (or select all) for every day.'
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
          name="capacityDelta"
          label="Seat change"
          extra="Signed change on top of the normal capacity, e.g. +30 for a summer garden or -10 for a partial closure."
          rules={[
            { required: true, message: 'A seat change is required.' },
            { type: 'integer', message: 'The seat change must be a whole number.' },
            {
              validator: (_, value: number) =>
                value === 0
                  ? Promise.reject(new Error('The seat change cannot be zero.'))
                  : Promise.resolve(),
            },
          ]}
        >
          <InputNumber step={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="description" label="Notes">
          <Input placeholder="e.g. Summer garden" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
