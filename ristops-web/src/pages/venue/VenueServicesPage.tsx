import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Empty, Flex, Result, Spin, theme } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { useListVenueServices } from '../../domain/service/service.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import ServiceCard from '../../components/service/ServiceCard.tsx';
import ServiceFormModal from '../../components/service/ServiceFormModal.tsx';

export default function VenueServicesPage() {
  const { venueId = '' } = useParams<{ venueId: string }>();
  const { token } = theme.useToken();
  const resource = { type: ResourceType.Venue, id: venueId };
  const { isAllowed: canList, isLoading: isLoadingCan } = useCan(
    resource,
    'service:list',
  );
  const { isAllowed: canAdd } = useCan(resource, 'service:add');

  const { data, isLoading } = useListVenueServices(venueId);
  const services = data?.listServices ?? [];

  const [addOpen, setAddOpen] = useState(false);

  if (isLoadingCan || isLoading) return <Spin />;
  if (!canList) {
    return (
      <Result status="403" title="You don't have permission to view services" />
    );
  }

  return (
    <>
      {services.length === 0 && !canAdd ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No services yet."
          style={{ marginTop: 64 }}
        />
      ) : (
        <Flex vertical gap={16} align="center">
          {services.map((service) => (
            <ServiceCard key={service.id} venueId={venueId} service={service} />
          ))}
          {canAdd && (
            <Card
              hoverable
              onClick={() => setAddOpen(true)}
              style={{
                width: '50%',
                borderStyle: 'dashed',
                color: token.colorTextSecondary,
              }}
              styles={{
                body: {
                  minHeight: 200,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                },
              }}
            >
              <PlusOutlined style={{ fontSize: 24 }} />
              Add service
            </Card>
          )}
        </Flex>
      )}

      <ServiceFormModal
        venueId={venueId}
        open={addOpen}
        onClose={() => setAddOpen(false)}
      />
    </>
  );
}
