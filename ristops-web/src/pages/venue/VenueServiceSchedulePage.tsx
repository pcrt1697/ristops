import { useNavigate, useParams } from 'react-router-dom';
import {
  Button,
  Descriptions,
  Divider,
  Flex,
  Result,
  Spin,
  Typography,
} from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { useService } from '../../domain/service/service.hooks.ts';
import { useServiceOpenings } from '../../domain/schedule/schedule.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import ServiceWeeklyHours from '../../components/service/ServiceWeeklyHours.tsx';
import { formatValidity } from '../../domain/schedule/schedule.utils.ts';

const { Title } = Typography;

export default function VenueServiceSchedulePage() {
  const { venueId = '', serviceId = '' } = useParams<{
    venueId: string;
    serviceId: string;
  }>();
  const navigate = useNavigate();

  const resource = { type: ResourceType.Service, id: serviceId };
  const { isAllowed: canList, isLoading: isLoadingCan } = useCan(
    resource,
    'schedule:list',
  );
  const { isAllowed: canEdit } = useCan(resource, 'schedule:edit');

  const { data: serviceData, isLoading: isLoadingService } =
    useService(serviceId);
  const service = serviceData?.service;
  const { data: openingsData, isLoading: isLoadingOpenings } =
    useServiceOpenings(serviceId);

  if (isLoadingCan || isLoadingService || isLoadingOpenings) return <Spin />;
  if (!canList) {
    return (
      <Result
        status="403"
        title="You don't have permission to view this schedule"
      />
    );
  }
  if (!service) return null;

  return (
    <>
      <Flex justify="space-between" align="center">
        <Title level={3} style={{ margin: 0 }}>
          {service.name}
        </Title>
        <Button
          type="link"
          size="small"
          icon={<ArrowLeftOutlined />}
          onClick={() => void navigate(`/venues/${venueId}/services`)}
        >
          Back to services
        </Button>
      </Flex>

      <Descriptions size="small" column={2} style={{ marginTop: 16 }}>
        <Descriptions.Item label="Runs">
          {formatValidity(service.dateFrom, service.dateTo)}
        </Descriptions.Item>
        <Descriptions.Item label="Capacity">
          {service.capacity} seats
        </Descriptions.Item>
      </Descriptions>

      <Divider titlePlacement="start" style={{ marginTop: 32 }}>
        Weekly hours
      </Divider>
      <ServiceWeeklyHours
        serviceId={serviceId}
        openings={openingsData ?? []}
        canEdit={canEdit}
      />
    </>
  );
}
