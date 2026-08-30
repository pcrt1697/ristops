import { DatePicker, Form, Input, InputNumber, Modal } from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
import {
  useCreateReservation,
  useUpdateReservation,
} from '../../domain/reservation/reservation.hooks.ts';
import type { SearchReservationsQuery } from '../../services/graphql/graphql.ts';
import AvailabilitySlotPicker from './AvailabilitySlotPicker.tsx';

type Reservation = SearchReservationsQuery['reservations']['items'][number];

interface ReservationFormValues {
  contactName: string;
  contactPhoneNumber?: string;
  contactEmail?: string;
  partySize: number;
  date: Dayjs;
  slotAt: string;
  notes?: string;
}

interface ReservationFormModalProps {
  venueId: string;
  /** Present when editing; omitted to create. */
  reservation?: Reservation;
  /** Date the day view is showing, used as the default for a new booking. */
  defaultDate?: string;
  open: boolean;
  onClose: () => void;
}

/**
 * Create or edit a booking. The time is not free-typed: it is picked from the availability
 * preview, so the form can only offer slots the backend would accept — the same rules it
 * re-validates under a lock on save.
 */
export default function ReservationFormModal({
  venueId,
  reservation,
  defaultDate,
  open,
  onClose,
}: ReservationFormModalProps) {
  const [form] = Form.useForm<ReservationFormValues>();
  const createReservation = useCreateReservation();
  const updateReservation = useUpdateReservation();
  const isEditing = !!reservation;
  const isPending = createReservation.isPending || updateReservation.isPending;

  // Watched so the slot picker re-queries as the date or party size changes.
  const date = Form.useWatch('date', form);
  const partySize = Form.useWatch('partySize', form);

  function handleCancel() {
    form.resetFields();
    onClose();
  }

  function handleSubmit() {
    form
      .validateFields()
      .then(async (values) => {
        if (reservation) {
          await updateReservation.mutateAsync({
            id: reservation.id,
            input: {
              contactName: values.contactName,
              contactPhoneNumber: values.contactPhoneNumber || null,
              partySize: values.partySize,
              reservationDate: values.slotAt,
              notes: values.notes || null,
            },
          });
        } else {
          await createReservation.mutateAsync({
            venueId,
            contactName: values.contactName,
            contactPhoneNumber: values.contactPhoneNumber || null,
            contactEmail: values.contactEmail || null,
            partySize: values.partySize,
            reservationDate: values.slotAt,
            notes: values.notes || null,
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
      title={isEditing ? 'Edit reservation' : 'New reservation'}
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={isPending}
      okText={isEditing ? 'Save' : 'Book'}
      width={640}
      destroyOnHidden
      afterOpenChange={(o) => {
        if (o) {
          const at = reservation ? dayjs(reservation.reservationDate) : undefined;
          form.setFieldsValue({
            contactName: reservation?.contactName ?? undefined,
            contactPhoneNumber: reservation?.contactPhoneNumber ?? undefined,
            contactEmail: reservation?.contactEmail ?? undefined,
            partySize: reservation?.partySize ?? 2,
            date: at ?? (defaultDate ? dayjs(defaultDate) : dayjs()),
            slotAt: at ? at.format('YYYY-MM-DDTHH:mm:00') : undefined,
            notes: reservation?.notes ?? undefined,
          });
        }
      }}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="contactName"
          label="Customer"
          rules={[{ required: true, message: 'A name is required.' }]}
        >
          <Input placeholder="e.g. M. Rossi" />
        </Form.Item>
        <Form.Item name="contactPhoneNumber" label="Phone">
          <Input placeholder="e.g. +39 333 1234567" />
        </Form.Item>
        <Form.Item
          name="contactEmail"
          label="Email"
          extra={
            isEditing
              ? 'The email cannot be changed after the booking is created.'
              : undefined
          }
        >
          <Input disabled={isEditing} placeholder="e.g. name@example.com" />
        </Form.Item>
        <Form.Item
          name="partySize"
          label="People"
          rules={[{ required: true, message: 'A party size is required.' }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item
          name="date"
          label="Date"
          rules={[{ required: true, message: 'A date is required.' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            // Changing the date invalidates the slot picked under the previous one.
            onChange={() => form.setFieldValue('slotAt', undefined)}
          />
        </Form.Item>
        <Form.Item
          name="slotAt"
          label="Service and time"
          // Only checked on confirm: picking a service is a step towards choosing a time, not a
          // failure to have chosen one.
          validateTrigger={[]}
          rules={[{ required: true, message: 'Pick an available time.' }]}
        >
          <AvailabilitySlotPicker
            venueId={venueId}
            businessDate={date ? date.format('YYYY-MM-DD') : undefined}
            partySize={partySize}
            excludeReservationId={reservation?.id}
            onServiceChange={() =>
              form.setFields([{ name: 'slotAt', value: undefined, errors: [] }])
            }
            onChange={(slotAt) =>
              // Clears the error a previous confirm may have raised, now that it is answered.
              form.setFields([{ name: 'slotAt', value: slotAt, errors: [] }])
            }
          />
        </Form.Item>
        <Form.Item name="notes" label="Notes">
          <Input.TextArea rows={2} placeholder="e.g. window table, birthday" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
