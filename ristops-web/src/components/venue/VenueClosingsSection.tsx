import { useState } from 'react';
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
  useDeleteVenueClosing,
  useSearchVenueClosingsPage,
} from '../../domain/schedule/schedule.hooks.ts';
import {
  formatDateRange,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import {
  ResourceType,
  type SearchVenueClosingsQuery,
} from '../../services/graphql/graphql.ts';
import VenueClosingFormModal from './VenueClosingFormModal.tsx';

const { Text } = Typography;
type VenueClosing = SearchVenueClosingsQuery['venueClosings']['items'][number];
const PAGE_SIZE = 8;

interface VenueClosingsSectionProps {
  venueId: string;
}

export default function VenueClosingsSection({
  venueId,
}: VenueClosingsSectionProps) {
  const { token } = theme.useToken();
  const resource = { type: ResourceType.Venue, id: venueId };
  const { isAllowed: canList } = useCan(resource, 'schedule:list');
  const { isAllowed: canEdit } = useCan(resource, 'schedule:edit');

  const [page, setPage] = useState(0);
  const { data, isFetching } = useSearchVenueClosingsPage(
    venueId,
    {},
    page,
    PAGE_SIZE,
  );
  const [editing, setEditing] = useState<VenueClosing>();
  const [modalOpen, setModalOpen] = useState(false);
  const remove = useDeleteVenueClosing(venueId);

  if (!canList) return null;

  const openAdd = () => {
    setEditing(undefined);
    setModalOpen(true);
  };
  const openEdit = (closing: VenueClosing) => {
    setEditing(closing);
    setModalOpen(true);
  };
  const confirmDelete = (closing: VenueClosing) =>
    Modal.confirm({
      title: 'Delete venue closure',
      icon: <ExclamationCircleFilled />,
      content: `Delete this venue closure (${formatDateRange(closing.dateStart, closing.dateEnd)})?`,
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: () => remove.mutateAsync(closing.id),
    });

  const columns: TableProps<VenueClosing>['columns'] = [
    {
      title: 'Dates',
      render: (_, r) => formatDateRange(r.dateStart, r.dateEnd),
    },
    {
      title: 'Applies to',
      render: (_, r) =>
        r.weekday ? `Every ${weekdayLabel(r.weekday)}` : 'Every day',
    },
    { title: 'Notes', render: (_, r) => r.description ?? '—' },
    ...(canEdit
      ? [
          {
            title: '',
            width: 84,
            render: (_: unknown, r: VenueClosing) => (
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
        <Text strong>Venue closures</Text>
        <div style={{ flex: 1, borderTop: `1px solid ${token.colorSplit}` }} />
        {canEdit && (
          <Button icon={<PlusOutlined />} onClick={openAdd}>
            Add closure
          </Button>
        )}
      </Flex>

      <Table<VenueClosing>
        rowKey="id"
        size="small"
        loading={isFetching}
        dataSource={data?.venueClosings.items ?? []}
        columns={columns}
        pagination={{
          current: page + 1,
          pageSize: PAGE_SIZE,
          total: data?.venueClosings.total ?? 0,
          showSizeChanger: false,
          hideOnSinglePage: true,
          onChange: (p) => setPage(p - 1),
        }}
      />

      {canEdit && (
        <VenueClosingFormModal
          venueId={venueId}
          closing={editing}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}
