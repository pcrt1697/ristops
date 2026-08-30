import { useState } from 'react';
import { Alert, Button, Flex, Select, Spin, Typography } from 'antd';
import dayjs from 'dayjs';
import { useReservationAvailability } from '../../domain/reservation/reservation.hooks.ts';
import type { ReservationAvailabilityQuery } from '../../services/graphql/graphql.ts';

const { Text } = Typography;

type ServiceAvailability =
  ReservationAvailabilityQuery['reservationAvailability']['services'][number];

/** Wire format of a reservation date: naive venue-local, to the minute. */
function slotValue(slotAt: string): string {
  return dayjs(slotAt).format('YYYY-MM-DDTHH:mm:00');
}

/** The most seats bookable at any one of a service's remaining slots. */
function bestRemaining(service: ServiceAvailability): number {
  return service.slots.reduce(
    (best, slot) => (slot.bookable && slot.remaining > best ? slot.remaining : best),
    0,
  );
}

interface AvailabilitySlotPickerProps {
  venueId: string;
  /** Selected date as `YYYY-MM-DD`; undefined until the form has one. */
  businessDate?: string;
  partySize?: number;
  /** Editing an existing booking: its own seats must not count against itself. */
  excludeReservationId?: string;
  /** Selected slot as a naive local `YYYY-MM-DDTHH:mm:00`. Injected by the wrapping Form.Item. */
  value?: string;
  onChange?: (slotAt: string) => void;
  /**
   * Drop the chosen time when the service changes. The owner clears it through the form rather
   * than through `onChange`, so the field empties without the change being mistaken for the user
   * emptying it themselves.
   */
  onServiceChange?: () => void;
}

/**
 * Service and time pickers for the booking form.
 *
 * The backend omits slots that have passed or fall inside the advance-notice window, so a past
 * date legitimately comes back with services but no slots — the empty state says so rather than
 * implying an error. Slots the party does not fit into are listed but disabled, so the user can
 * see *why* a time is unavailable instead of finding it missing.
 */
export default function AvailabilitySlotPicker({
  venueId,
  businessDate,
  partySize,
  excludeReservationId,
  value,
  onChange,
  onServiceChange,
}: AvailabilitySlotPickerProps) {
  const [pickedServiceId, setPickedServiceId] = useState<string>();
  const query = useReservationAvailability(
    venueId,
    businessDate,
    partySize,
    excludeReservationId,
  );

  if (!businessDate || !partySize) {
    return (
      <Text type="secondary">Pick a date and party size to see available times.</Text>
    );
  }

  if (query.isError) {
    return (
      <Alert
        type="warning"
        showIcon
        message="Couldn't load available times"
        action={
          <Button size="small" onClick={() => void query.refetch()}>
            Retry
          </Button>
        }
      />
    );
  }

  if (query.isPending) {
    return (
      <Spin size="small">
        <div style={{ height: 32 }} />
      </Spin>
    );
  }

  const availability = query.data;
  const services = availability.services;

  if (availability.closed) {
    return <Alert type="info" showIcon message="The venue is closed on this date." />;
  }
  if (services.length === 0) {
    return (
      <Alert type="info" showIcon message="No service is scheduled on this date." />
    );
  }
  if (services.every((service) => service.slots.length === 0)) {
    return (
      <Alert type="info" showIcon message="No bookable slots remain for this date." />
    );
  }

  // Resolve the service without an effect: an explicit pick wins, else the one holding the
  // already-selected slot (editing), else the only service open that day. A pick that no longer
  // matches — after changing the date — falls through to undefined rather than sticking.
  const service =
    services.find((s) => s.serviceId === pickedServiceId) ??
    (value ? services.find((s) => s.slots.some((sl) => slotValue(sl.slotAt) === value)) : undefined) ??
    (services.length === 1 ? services[0] : undefined);

  function selectService(serviceId: string) {
    setPickedServiceId(serviceId);
    // The previously chosen time belongs to the previous service.
    onServiceChange?.();
  }

  return (
    <Flex vertical gap={8}>
      <Select
        placeholder="Select a service"
        value={service?.serviceId}
        onChange={selectService}
        options={services.map((option) => ({
          value: option.serviceId,
          label: option.serviceName,
          disabled: option.slots.length === 0,
          service: option,
        }))}
        optionRender={({ data }) => {
          const option = data.service;
          const seats = bestRemaining(option);
          return (
            <Flex vertical>
              <Text>{option.serviceName}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {dayjs(option.opensAt).format('HH:mm')}–
                {dayjs(option.closesAt).format('HH:mm')} ·{' '}
                {seats > 0
                  ? `up to ${seats} of ${option.capacity} seats free`
                  : 'fully booked'}
              </Text>
            </Flex>
          );
        }}
      />

      <Select
        placeholder={service ? 'Select a time' : 'Select a service first'}
        disabled={!service}
        value={value}
        onChange={onChange}
        options={(service?.slots ?? []).map((slot) => ({
          value: slotValue(slot.slotAt),
          label: dayjs(slot.slotAt).format('HH:mm'),
          disabled: !slot.bookable,
          remaining: slot.remaining,
        }))}
        optionRender={({ data, label }) => (
          <Flex justify="space-between" gap={12}>
            <Text>{label}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {data.remaining > 0 ? `${data.remaining} seats free` : 'full'}
            </Text>
          </Flex>
        )}
      />
    </Flex>
  );
}
