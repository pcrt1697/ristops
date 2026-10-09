import { useMemo, useState } from 'react';
import {
  Button,
  Flex,
  Modal,
  Space,
  Table,
  type TableProps,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleFilled,
  PlusOutlined,
} from '@ant-design/icons';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import {
  useDeleteClosing,
  useSearchClosings,
} from '../../domain/schedule/schedule.hooks.ts';
import { formatDateRange } from '../../domain/schedule/schedule.utils.ts';
import { useListVenueServices } from '../../domain/service/service.hooks.ts';
import {
  ResourceType,
  type SearchClosingsQuery,
} from '../../services/graphql/graphql.ts';
import ClosingFormModal from './ClosingFormModal.tsx';

const { Text } = Typography;
type Closing = SearchClosingsQuery['venueClosings']['items'][number];
const PAGE_SIZE = 8;

interface ClosingsSectionProps {
  venueId: string;
}

/** The venue's closures: which services are off the calendar, and when. */
export default function ClosingsSection({ venueId }: ClosingsSectionProps) {
  const { token } = theme.useToken();
  const resource = { type: ResourceType.Venue, id: venueId };
  const { isAllowed: canList } = useCan(resource, 'schedule:list');
  const { isAllowed: canEdit } = useCan(resource, 'schedule:edit');

  const [page, setPage] = useState(0);
  const { data, isFetching } = useSearchClosings(venueId, {
    pagination: { page, pageSize: PAGE_SIZE },
  });
  const { data: services } = useListVenueServices(venueId);
  const [editing, setEditing] = useState<Closing>();
  const [modalOpen, setModalOpen] = useState(false);
  const remove = useDeleteClosing(venueId);

  const serviceNames = useMemo(
    () =>
      new Map((services?.listServices ?? []).map((s) => [s.id, s.name])),
    [services],
  );

  if (!canList) return null;

  const openAdd = () => {
    setEditing(undefined);
    setModalOpen(true);
  };
  const openEdit = (closing: Closing) => {
    setEditing(closing);
    setModalOpen(true);
  };
  const confirmDelete = (closing: Closing) =>
    Modal.confirm({
      title: 'Delete closure',
      icon: <ExclamationCircleFilled />,
      content: `Delete this closure (${formatDateRange(closing.dateFrom, closing.dateTo)})?`,
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: () => remove.mutateAsync(closing.id),
    });

  const columns: TableProps<Closing>['columns'] = [
    {
      title: 'Dates',
      render: (_, r) => formatDateRange(r.dateFrom, r.dateTo),
    },
    {
      title: 'Closes',
      render: (_, r) => {
        const total = services?.listServices.length ?? 0;
        if (total > 0 && r.serviceIds.length === total) {
          return 'Every service';
        }
        return (
          r.serviceIds
            .map((id) => serviceNames.get(id) ?? id)
            .join(', ') || '—'
        );
      },
    },
    { title: 'Notes', render: (_, r) => r.description ?? '—' },
    ...(canEdit
      ? [
          {
            title: '',
            width: 84,
            render: (_: unknown, r: Closing) => (
              <Space>
                <Tooltip title="Edit">
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => openEdit(r)}
                  />
                </Tooltip>
                <Tooltip title="Delete">
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => confirmDelete(r)}
                  />
                </Tooltip>
              </Space>
            ),
          },
        ]
      : []),
  ];

  return (
    <>
      <Flex align="center" gap={16} style={{ marginTop: 48, marginBottom: 24 }}>
        <Text strong>Closures</Text>
        <div style={{ flex: 1, borderTop: `1px solid ${token.colorSplit}` }} />
        {canEdit && (
          <Button icon={<PlusOutlined />} onClick={openAdd}>
            Add closure
          </Button>
        )}
      </Flex>

      <Table<Closing>
        rowKey="id"
        size="small"
        loading={isFetching}
        dataSource={data?.items ?? []}
        columns={columns}
        pagination={{
          current: page + 1,
          pageSize: PAGE_SIZE,
          total: data?.total ?? 0,
          showSizeChanger: false,
          hideOnSinglePage: true,
          onChange: (p) => setPage(p - 1),
        }}
      />

      {canEdit && (
        <ClosingFormModal
          venueId={venueId}
          closing={editing}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}
