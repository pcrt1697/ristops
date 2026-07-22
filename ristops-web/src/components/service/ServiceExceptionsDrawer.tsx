import { useState } from 'react';
import {
  Button,
  DatePicker,
  Drawer,
  Modal,
  Space,
  Table,
  type TableProps,
  Tabs,
  Tooltip,
  Typography,
} from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleFilled,
} from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import {
  useDeleteCapacityOverride,
  useDeleteServiceClosing,
  useDeleteOpeningOverride,
  useSearchCapacityOverridesPage,
  useSearchServiceClosingsPage,
  useSearchOpeningOverridesPage,
} from '../../domain/schedule/schedule.hooks.ts';
import {
  formatCapacityDelta,
  formatDateRange,
  formatTimeRange,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import type {
  SearchCapacityOverridesQuery,
  SearchServiceClosingsQuery,
  SearchOpeningOverridesQuery,
  Weekday,
} from '../../services/graphql/graphql.ts';
import OverrideFormModal from './OverrideFormModal.tsx';
import ServiceClosingFormModal from './ServiceClosingFormModal.tsx';
import CapacityFormModal from './CapacityFormModal.tsx';

const { Text } = Typography;
const PAGE_SIZE = 10;

type Override =
  SearchOpeningOverridesQuery['serviceOpeningOverrides']['items'][number];
type ServiceClosing =
  SearchServiceClosingsQuery['serviceClosings']['items'][number];
type CapacityOverride =
  SearchCapacityOverridesQuery['serviceCapacityOverrides']['items'][number];

interface ServiceExceptionsDrawerProps {
  serviceId: string;
  canEdit: boolean;
  open: boolean;
  onClose: () => void;
}

export default function ServiceExceptionsDrawer({
  serviceId,
  canEdit,
  open,
  onClose,
}: ServiceExceptionsDrawerProps) {
  const [dates, setDates] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const dateFrom = dates?.[0]?.format('YYYY-MM-DD');
  const dateTo = dates?.[1]?.format('YYYY-MM-DD');

  return (
    <Drawer
      title="All exceptions"
      placement="right"
      size={'80%'}
      open={open}
      onClose={onClose}
      styles={{ body: { paddingTop: 12 } }}
    >
      <DatePicker.RangePicker
        allowEmpty={[true, true]}
        value={dates}
        onChange={setDates}
        placeholder={['From (optional)', 'To (optional)']}
        style={{ marginBottom: 12 }}
      />
      <Tabs
        items={[
          {
            key: 'overrides',
            label: 'Overrides',
            children: (
              <OverridesTab
                serviceId={serviceId}
                canEdit={canEdit}
                dateFrom={dateFrom}
                dateTo={dateTo}
              />
            ),
          },
          {
            key: 'closings',
            label: 'Closings',
            children: (
              <ClosingsTab
                serviceId={serviceId}
                canEdit={canEdit}
                dateFrom={dateFrom}
                dateTo={dateTo}
              />
            ),
          },
          {
            key: 'capacity',
            label: 'Capacity',
            children: (
              <CapacityTab
                serviceId={serviceId}
                canEdit={canEdit}
                dateFrom={dateFrom}
                dateTo={dateTo}
              />
            ),
          },
        ]}
      />
    </Drawer>
  );
}

interface TabProps {
  serviceId: string;
  canEdit: boolean;
  dateFrom?: string;
  dateTo?: string;
}

/** Reset to the first page whenever the date filter changes. */
function usePagedState(dateFrom?: string, dateTo?: string) {
  const [page, setPage] = useState(0);
  const key = `${dateFrom ?? ''}|${dateTo ?? ''}`;
  const [prevKey, setPrevKey] = useState(key);
  if (key !== prevKey) {
    setPrevKey(key);
    setPage(0);
  }
  return { page, setPage };
}

function appliesTo(item: { weekday?: Weekday | null }): string {
  return item.weekday ? `Every ${weekdayLabel(item.weekday)}` : 'Every day';
}

function serverPagination<T>(
  page: number,
  total: number,
  setPage: (p: number) => void,
): TableProps<T>['pagination'] {
  return {
    current: page + 1,
    pageSize: PAGE_SIZE,
    total,
    showSizeChanger: false,
    hideOnSinglePage: true,
    onChange: (p) => setPage(p - 1),
  };
}

function OverridesTab({ serviceId, canEdit, dateFrom, dateTo }: TabProps) {
  const { page, setPage } = usePagedState(dateFrom, dateTo);
  const { data, isFetching } = useSearchOpeningOverridesPage(
    serviceId,
    { dateFrom, dateTo },
    page,
    PAGE_SIZE,
  );
  const [editing, setEditing] = useState<Override>();
  const [modalOpen, setModalOpen] = useState(false);
  const remove = useDeleteOpeningOverride(serviceId);

  const columns: TableProps<Override>['columns'] = [
    {
      title: 'Dates',
      render: (_, r) => formatDateRange(r.dateStart, r.dateEnd),
    },
    { title: 'Applies to', render: (_, r) => appliesTo(r) },
    {
      title: 'Hours',
      render: (_, r) => formatTimeRange(r.startTime, r.endTime),
    },
    { title: 'Capacity', dataIndex: 'capacity' },
    { title: 'Notes', render: (_, r) => r.description ?? '—' },
    ...rowActions<Override>(canEdit, {
      onEdit: (r) => {
        setEditing(r);
        setModalOpen(true);
      },
      onDelete: (r) =>
        confirmDelete('override', r.dateStart, r.dateEnd, () =>
          remove.mutateAsync(r.id),
        ),
    }),
  ];

  return (
    <>
      <Table<Override>
        rowKey="id"
        size="small"
        loading={isFetching}
        dataSource={data?.serviceOpeningOverrides.items ?? []}
        columns={columns}
        pagination={serverPagination<Override>(
          page,
          data?.serviceOpeningOverrides.total ?? 0,
          setPage,
        )}
      />
      {canEdit && (
        <OverrideFormModal
          serviceId={serviceId}
          override={editing}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}

function ClosingsTab({ serviceId, canEdit, dateFrom, dateTo }: TabProps) {
  const { page, setPage } = usePagedState(dateFrom, dateTo);
  const { data, isFetching } = useSearchServiceClosingsPage(
    serviceId,
    { dateFrom, dateTo },
    page,
    PAGE_SIZE,
  );
  const [editing, setEditing] = useState<ServiceClosing>();
  const [modalOpen, setModalOpen] = useState(false);
  const remove = useDeleteServiceClosing(serviceId);

  const columns: TableProps<ServiceClosing>['columns'] = [
    {
      title: 'Dates',
      render: (_, r) => formatDateRange(r.dateStart, r.dateEnd),
    },
    { title: 'Applies to', render: (_, r) => appliesTo(r) },
    { title: 'Notes', render: (_, r) => r.description ?? '—' },
    ...rowActions<ServiceClosing>(canEdit, {
      onEdit: (r) => {
        setEditing(r);
        setModalOpen(true);
      },
      onDelete: (r) =>
        confirmDelete('closing', r.dateStart, r.dateEnd, () =>
          remove.mutateAsync(r.id),
        ),
    }),
  ];

  return (
    <>
      <Table<ServiceClosing>
        rowKey="id"
        size="small"
        loading={isFetching}
        dataSource={data?.serviceClosings.items ?? []}
        columns={columns}
        pagination={serverPagination<ServiceClosing>(
          page,
          data?.serviceClosings.total ?? 0,
          setPage,
        )}
      />
      {canEdit && (
        <ServiceClosingFormModal
          serviceId={serviceId}
          closing={editing}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}

function CapacityTab({ serviceId, canEdit, dateFrom, dateTo }: TabProps) {
  const { page, setPage } = usePagedState(dateFrom, dateTo);
  const { data, isFetching } = useSearchCapacityOverridesPage(
    serviceId,
    { dateFrom, dateTo },
    page,
    PAGE_SIZE,
  );
  const [editing, setEditing] = useState<CapacityOverride>();
  const [modalOpen, setModalOpen] = useState(false);
  const remove = useDeleteCapacityOverride(serviceId);

  const columns: TableProps<CapacityOverride>['columns'] = [
    {
      title: 'Dates',
      render: (_, r) => formatDateRange(r.dateStart, r.dateEnd),
    },
    { title: 'Applies to', render: (_, r) => appliesTo(r) },
    {
      title: 'Seat change',
      render: (_, r) => formatCapacityDelta(r.capacityDelta),
    },
    { title: 'Notes', render: (_, r) => r.description ?? '—' },
    ...rowActions<CapacityOverride>(canEdit, {
      onEdit: (r) => {
        setEditing(r);
        setModalOpen(true);
      },
      onDelete: (r) =>
        confirmDelete('capacity change', r.dateStart, r.dateEnd, () =>
          remove.mutateAsync(r.id),
        ),
    }),
  ];

  return (
    <>
      <Table<CapacityOverride>
        rowKey="id"
        size="small"
        loading={isFetching}
        dataSource={data?.serviceCapacityOverrides.items ?? []}
        columns={columns}
        pagination={serverPagination<CapacityOverride>(
          page,
          data?.serviceCapacityOverrides.total ?? 0,
          setPage,
        )}
      />
      {canEdit && (
        <CapacityFormModal
          serviceId={serviceId}
          capacityOverride={editing}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}

function rowActions<T>(
  canEdit: boolean,
  handlers: { onEdit: (r: T) => void; onDelete: (r: T) => void },
): NonNullable<TableProps<T>['columns']> {
  if (!canEdit) return [];
  return [
    {
      title: '',
      width: 84,
      render: (_, r: T) => (
        <Space>
          <Tooltip title="Edit">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handlers.onEdit(r)}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handlers.onDelete(r)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];
}

function confirmDelete(
  kind: string,
  dateStart: string,
  dateEnd: string,
  onOk: () => Promise<unknown>,
) {
  Modal.confirm({
    title: `Delete ${kind}`,
    icon: <ExclamationCircleFilled />,
    content: (
      <Text>
        Delete this {kind} ({formatDateRange(dateStart, dateEnd)})?
      </Text>
    ),
    okText: 'Delete',
    okButtonProps: { danger: true },
    onOk,
  });
}
