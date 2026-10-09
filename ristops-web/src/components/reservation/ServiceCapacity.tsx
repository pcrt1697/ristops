import { Flex, Tag, Typography, theme } from 'antd';
import dayjs from 'dayjs';
import type { ReservationCalendarQuery } from '../../services/graphql/graphql.ts';

const { Text } = Typography;

type CalendarDay = ReservationCalendarQuery['reservationCalendar'][number];
export type ServiceSummary = CalendarDay['services'][number];
export type UnavailableService = Pick<
  CalendarDay['closedServices'][number],
  'serviceName' | 'reservationCount'
>;

/** Why a service is no longer running on a day it still holds bookings. */
export type UnavailableReason = 'closed' | 'deleted';

/** One running service's occupancy, from the calendar summary rather than the loaded rows. */
export default function ServiceCapacity({ service }: { service: ServiceSummary }) {
  const { token } = theme.useToken();
  const fill =
    service.capacity > 0
      ? Math.min(1, service.booked / service.capacity)
      : 0;
  const color = service.overCapacity ? token.colorError : token.colorPrimary;

  return (
    <div style={{ minWidth: 200 }}>
      <Flex justify="space-between" align="center" gap={12}>
        <Flex align="center" gap={6}>
          <Text style={{ fontSize: 13 }}>{service.serviceName}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {dayjs(service.opensAt).format('HH:mm')}–
            {dayjs(service.closesAt).format('HH:mm')}
          </Text>
          {service.overCapacity && (
            <Tag color="error" style={{ margin: 0 }}>
              Over capacity
            </Tag>
          )}
        </Flex>
        <Text
          style={{
            fontSize: 13,
            color: service.overCapacity ? color : undefined,
          }}
        >
          {service.booked}/{service.capacity} seats
        </Text>
      </Flex>
      <div
        style={{
          height: 4,
          marginTop: 4,
          borderRadius: 2,
          background: token.colorFillSecondary,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${fill * 100}%`,
            borderRadius: 2,
            background: color,
          }}
        />
      </div>
    </div>
  );
}

interface UnavailableServiceNoticeProps {
  service: UnavailableService;
  reason: UnavailableReason;
}

/** A service that no longer runs that day but still holds bookings. A deleted one is struck through. */
export function UnavailableServiceNotice({ service, reason }: UnavailableServiceNoticeProps) {
  const count = service.reservationCount;
  const deleted = reason === 'deleted';

  return (
    <div style={{ minWidth: 200 }}>
      <Flex justify="space-between" align="center" gap={12}>
        <Text delete={deleted} style={{ fontSize: 13 }}>
          {service.serviceName}
        </Text>
        <Tag color={deleted ? 'error' : 'warning'} style={{ margin: 0 }}>
          {deleted ? 'Deleted' : 'Closed'}
        </Tag>
      </Flex>
      <Text type="secondary" style={{ fontSize: 12 }}>
        {count} {count === 1 ? 'reservation needs' : 'reservations need'} attention
      </Text>
    </div>
  );
}
