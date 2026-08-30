import {
  Button,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  theme,
  type TableProps,
} from 'antd';
import { EditOutlined, ExclamationCircleFilled } from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  EDITABLE_STATUSES,
  STATUS_COLOR,
  VIOLATION_LABEL,
  statusLabel,
} from '../../domain/reservation/reservation.utils.ts';
import { type SearchReservationsQuery } from '../../services/graphql/graphql.ts';
import ReservationStatusActions from './ReservationStatusActions.tsx';

const { Text } = Typography;

type Reservation = SearchReservationsQuery['reservations']['items'][number];

/** A booking paired with the service window it resolved to. */
export interface ReservationRow {
  reservation: Reservation;
  service?: { serviceId: string; serviceName: string };
}

const ROWS_PER_PAGE = 20;

interface ReservationTableProps {
  venueId: string;
  rows: ReservationRow[];
  /** Show the service column; hidden when the pane is already filtered to one service. */
  showService: boolean;
  canEdit: boolean;
  onEdit: (reservation: Reservation) => void;
}

/** The day's bookings, ordered by time across every service. */
export default function ReservationTable({
  venueId,
  rows,
  showService,
  canEdit,
  onEdit,
}: ReservationTableProps) {
  const { token } = theme.useToken();

  const columns: TableProps<ReservationRow>['columns'] = [
    {
      title: 'Time',
      key: 'time',
      width: 90,
      render: (_, { reservation }) => (
        <>
          <Text strong>{dayjs(reservation.reservationDate).format('HH:mm')}</Text>
          {reservation.violation && (
            <Tooltip title={VIOLATION_LABEL[reservation.violation]}>
              <ExclamationCircleFilled
                style={{ marginLeft: 6, color: token.colorWarning }}
              />
            </Tooltip>
          )}
        </>
      ),
    },
    ...(showService
      ? [
          {
            title: 'Service',
            key: 'service',
            render: (_: unknown, { service }: ReservationRow) => (
              <Text type="secondary">{service?.serviceName}</Text>
            ),
          } satisfies NonNullable<TableProps<ReservationRow>['columns']>[number],
        ]
      : []),
    {
      title: 'People',
      key: 'partySize',
      width: 80,
      render: (_, { reservation }) => reservation.partySize,
    },
    {
      title: 'Customer',
      key: 'contactName',
      render: (_, { reservation }) => reservation.contactName,
    },
    {
      title: 'Contact',
      key: 'contact',
      render: (_, { reservation }) => (
        <Text type="secondary">
          {[reservation.contactPhoneNumber, reservation.contactEmail]
            .filter(Boolean)
            .join(' · ') || '—'}
        </Text>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 130,
      render: (_, { reservation }) => (
        <>
          <Tag color={STATUS_COLOR[reservation.status]}>
            {statusLabel(reservation.status)}
          </Tag>
          {reservation.arrivalTime && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {reservation.arrivalTime.slice(0, 5)}
            </Text>
          )}
        </>
      ),
    },
    {
      key: 'actions',
      width: 88,
      align: 'right',
      render: (_, { reservation }) => (
        <Space size={0}>
          {canEdit && EDITABLE_STATUSES.includes(reservation.status) && (
            <Tooltip title="Edit">
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => onEdit(reservation)}
              />
            </Tooltip>
          )}
          <ReservationStatusActions venueId={venueId} reservation={reservation} />
        </Space>
      ),
    },
  ];

  return (
    <Table<ReservationRow>
      rowKey={({ reservation }) => reservation.id}
      size="small"
      columns={columns}
      dataSource={rows}
      pagination={rows.length > ROWS_PER_PAGE ? { pageSize: ROWS_PER_PAGE } : false}
      expandable={{
        // Notes are the only long field; keeping them out of the row preserves the time
        // column's alignment, which is what staff scan during service.
        expandedRowRender: ({ reservation }) => <Text>{reservation.notes}</Text>,
        rowExpandable: ({ reservation }) => !!reservation.notes,
      }}
    />
  );
}
