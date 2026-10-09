import { useEffect } from 'react';
import { DatePicker, Form, Input, InputNumber, Modal, Select, TimePicker, Typography } from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
import {
  useCreateReservation,
  useReservationCalendar,
  useUpdateReservation,
} from '../../domain/reservation/reservation.hooks.ts';
import type {
  ReservationCalendarQuery,
  SearchReservationsQuery,
} from '../../services/graphql/graphql.ts';

const { Text } = Typography;

type Reservation = SearchReservationsQuery['reservations']['items'][number];
type ServiceSummary =
  ReservationCalendarQuery['reservationCalendar'][number]['services'][number];

interface ReservationFormValues {
  contactName: string;
  contactPhoneNumber?: string;
  contactEmail?: string;
  partySize: number;
  date: Dayjs;
  serviceId: string;
  time: Dayjs;
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
 * The wall-clock instant a time lands on within a service's window.
 *
 * The picked time is placed on the window's opening date, then pushed to the following day when
 * that would put it before the opening — which is what makes 00:30 resolve into the tail of an
 * overnight service rather than an hour before it opened.
 */
function instantWithin(service: ServiceSummary, time: Dayjs): Dayjs {
  const opens = dayjs(service.opensAt);
  const at = opens.hour(time.hour()).minute(time.minute()).second(0).millisecond(0);
  return at.isBefore(opens) ? at.add(1, 'day') : at;
}

function withinWindow(service: ServiceSummary, time: Dayjs): boolean {
  const at = instantWithin(service, time);
  return !at.isBefore(dayjs(service.opensAt)) && at.isBefore(dayjs(service.closesAt));
}

/**
 * Create or edit a booking.
 *
 * A booking names its service, so the form picks one from the services running that date and
 * then any time inside its window — there is no slot grid. The remaining seats shown per service
 * come from the day's calendar summary; the backend re-checks the window and the capacity under
 * a lock on save, so this only keeps the obviously-wrong out.
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

  // Watched so the service list follows the date, and the time field can be bounded by the
  // service the user settles on.
  const date = Form.useWatch('date', form);
  const serviceId = Form.useWatch('serviceId', form);

  const businessDate = date ? date.format('YYYY-MM-DD') : '';
  const { data: days } = useReservationCalendar(
    venueId,
    businessDate,
    businessDate,
    open && !!businessDate,
  );
  const day = days?.[0];
  const services = day?.services ?? [];
  const service = services.find((s) => s.serviceId === serviceId);

  // An edited booking may sit on a service that no longer runs that day, being closed or
  // deleted, so it is not on offer. Leave the field empty then, so a new service is picked.
  const serviceOffered = services.some((s) => s.serviceId === serviceId);
  useEffect(() => {
    if (days && serviceId && !serviceOffered) {
      form.setFieldValue('serviceId', undefined);
      form.setFieldValue('time', undefined);
    }
  }, [days, serviceId, serviceOffered, form]);

  function handleCancel() {
    form.resetFields();
    onClose();
  }

  function handleSubmit() {
    form
      .validateFields()
      .then(async (values) => {
        const picked = services.find((s) => s.serviceId === values.serviceId);
        if (!picked) return;
        const reservationDate = instantWithin(picked, values.time).format(
          'YYYY-MM-DDTHH:mm:00',
        );
        if (reservation) {
          await updateReservation.mutateAsync({
            id: reservation.id,
            input: {
              serviceId: values.serviceId,
              contactName: values.contactName,
              contactPhoneNumber: values.contactPhoneNumber || null,
              partySize: values.partySize,
              reservationDate,
              notes: values.notes || null,
            },
          });
        } else {
          await createReservation.mutateAsync({
            venueId,
            serviceId: values.serviceId,
            contactName: values.contactName,
            contactPhoneNumber: values.contactPhoneNumber || null,
            contactEmail: values.contactEmail || null,
            partySize: values.partySize,
            reservationDate,
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
            serviceId: reservation?.serviceId ?? undefined,
            time: at ?? undefined,
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
          extra="For a service running past midnight, this is the date it opens on."
          rules={[{ required: true, message: 'A date is required.' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            // The services on offer change with the date, so a service picked under the
            // previous one no longer means anything.
            onChange={() =>
              form.setFields([
                { name: 'serviceId', value: undefined, errors: [] },
                { name: 'time', value: undefined, errors: [] },
              ])
            }
          />
        </Form.Item>
        <Form.Item
          name="serviceId"
          label="Service"
          extra={
            day?.closed
              ? 'Every service is closed on this date.'
              : services.length === 0
                ? 'No service runs on this date.'
                : undefined
          }
          rules={[{ required: true, message: 'Pick a service.' }]}
        >
          <Select
            placeholder="Pick a service"
            disabled={services.length === 0}
            onChange={() => form.setFields([{ name: 'time', value: undefined, errors: [] }])}
            options={services.map((s) => ({
              value: s.serviceId,
              label: (
                <>
                  {s.serviceName}{' '}
                  <Text type="secondary">
                    {dayjs(s.opensAt).format('HH:mm')}–{dayjs(s.closesAt).format('HH:mm')} ·{' '}
                    {Math.max(0, s.remaining)} of {s.capacity} seats left
                  </Text>
                </>
              ),
            }))}
          />
        </Form.Item>
        <Form.Item
          name="time"
          label="Time"
          extra={
            service
              ? `Any time between ${dayjs(service.opensAt).format('HH:mm')} and ${dayjs(
                  service.closesAt,
                ).format('HH:mm')}.`
              : 'Pick a service first.'
          }
          dependencies={['serviceId']}
          rules={[
            { required: true, message: 'A time is required.' },
            () => ({
              validator(_, value: Dayjs | undefined) {
                if (!value || !service || withinWindow(service, value)) {
                  return Promise.resolve();
                }
                return Promise.reject(
                  new Error('That time is outside the service opening hours.'),
                );
              },
            }),
          ]}
        >
          <TimePicker
            style={{ width: '100%' }}
            format="HH:mm"
            minuteStep={5}
            needConfirm={false}
            disabled={!service}
          />
        </Form.Item>
        <Form.Item name="notes" label="Notes">
          <Input.TextArea rows={2} placeholder="e.g. window table, birthday" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
