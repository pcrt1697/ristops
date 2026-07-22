import { type ReactNode, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Descriptions, Modal, theme, Tooltip } from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  ExclamationCircleFilled,
  ScheduleOutlined,
} from '@ant-design/icons';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { useDeleteService } from '../../domain/service/service.hooks.ts';
import type { ListServicesQuery } from '../../services/graphql/graphql.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import ServiceFormModal from './ServiceFormModal.tsx';

type ServiceListItem = ListServicesQuery['listServices'][number];

interface ServiceCardProps {
  venueId: string;
  service: ServiceListItem;
}

export default function ServiceCard({ venueId, service }: ServiceCardProps) {
  const { token } = theme.useToken();
  const resource = { type: ResourceType.Service, id: service.id };
  const { isAllowed: canEdit } = useCan(resource, 'service:edit');
  const { isAllowed: canViewSchedule } = useCan(resource, 'schedule:get');
  const { isAllowed: canRemove } = useCan(resource, 'service:remove');

  const [editOpen, setEditOpen] = useState(false);
  const navigate = useNavigate();
  const deleteService = useDeleteService(venueId);

  const confirmDelete = () => {
    Modal.confirm({
      title: 'Delete service',
      icon: <ExclamationCircleFilled />,
      content: `Delete "${service.name}"? This cannot be undone.`,
      okText: 'Delete',
      okButtonProps: { danger: true, loading: deleteService.isPending },
      onOk: () => deleteService.mutateAsync(service.id),
    });
  };

  const actions: ReactNode[] = [];
  if (canViewSchedule) {
    actions.push(
      <Tooltip key="schedule" title="Go to schedule">
        <ScheduleOutlined
          style={{ color: token.colorPrimary }}
          onClick={() =>
            void navigate(`/venues/${venueId}/services/${service.id}/schedule`)
          }
        />
      </Tooltip>,
    );
  }
  if (canEdit) {
    actions.push(
      <Tooltip key="edit" title="Edit service details">
        <EditOutlined
          style={{ color: token.colorPrimary }}
          onClick={() => setEditOpen(true)}
        />
      </Tooltip>,
    );
  }
  if (canRemove) {
    actions.push(
      <Tooltip key="delete" title="Delete service">
        <DeleteOutlined
          style={{ color: token.colorError }}
          onClick={confirmDelete}
        />
      </Tooltip>,
    );
  }

  return (
    <>
      <Card
        style={{ width: '75%' }}
        actions={actions.length > 0 ? actions : undefined}
      >
        <Card.Meta
          title={service.name}
          description={service.description ?? undefined}
        />
        <Descriptions column={2} size="small" style={{ marginTop: 16 }}>
          <Descriptions.Item label="Turn time">
            {service.turnTimeM} min
          </Descriptions.Item>
          <Descriptions.Item label="Slot interval">
            {service.slotIntervalM} min
          </Descriptions.Item>
          <Descriptions.Item label="Min notice">
            {service.advanceNoticeM} min
          </Descriptions.Item>
          <Descriptions.Item label="Grace period">
            {service.gracePeriodM} min
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {canEdit && (
        <ServiceFormModal
          venueId={venueId}
          service={service}
          open={editOpen}
          onClose={() => setEditOpen(false)}
        />
      )}
    </>
  );
}
