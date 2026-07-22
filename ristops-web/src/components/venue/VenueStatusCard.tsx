import { useState } from 'react';
import {
  Button,
  Card,
  Divider,
  Input,
  Modal,
  Space,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import {
  useActivateVenue,
  useCloseVenue,
  useDisableVenue,
  useEnableVenue,
} from '../../domain/venue/venue.hooks.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { useListVenueServices } from '../../domain/service/service.hooks.ts';
import {
  type GetVenueQuery,
  ResourceType,
  VenueStatus,
} from '../../services/graphql/graphql.ts';

const { Text } = Typography;

interface VenueStatusCardProps {
  venue: GetVenueQuery['venue'];
}

export default function VenueStatusCard({ venue }: VenueStatusCardProps) {
  const { token } = theme.useToken();
  // Shares the ['service.list', venueId] cache with the services view, so this
  // does not trigger a second request — a venue needs at least one service
  // before it can be activated.
  const { data: servicesData } = useListVenueServices(venue.id);
  const serviceCount = servicesData?.listServices.length ?? 0;
  const resource = { type: ResourceType.Venue, id: venue.id };
  const { isAllowed: canActivate } = useCan(resource, 'venue:activate');
  const { isAllowed: canClose } = useCan(resource, 'venue:close');
  const { isAllowed: canDisable } = useCan(resource, 'venue:disable');
  const { isAllowed: canEnable } = useCan(resource, 'venue:enable');

  const { mutate: activateVenue, isPending: isActivating } = useActivateVenue();
  const { mutate: closeVenue, isPending: isClosing } = useCloseVenue();
  const { mutate: disableVenue, isPending: isDisabling } = useDisableVenue();
  const { mutate: enableVenue, isPending: isEnabling } = useEnableVenue();

  const [closeOpen, setCloseOpen] = useState(false);
  const [confirmName, setConfirmName] = useState('');

  const closeCloseModal = () => {
    setConfirmName('');
    setCloseOpen(false);
  };

  if (!canActivate && !canClose && !canDisable && !canEnable) return null;

  return (
    <>
      <Divider titlePlacement="start" style={{ marginTop: 48 }}>
        Status
      </Divider>
      <Card
        styles={{
          body: {
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            flexWrap: 'wrap',
          },
        }}
        style={{
          borderColor:
            venue.status === VenueStatus.Disabled
              ? token.colorError
              : undefined,
        }}
      >
        <div style={{ flex: 1 }}>
          <Text strong>Manage venue status</Text>
          <br />
          <Text type="secondary">
            Activate, close, disable, or re-enable this venue depending on its
            current status.
          </Text>
        </div>
        <Space>
          {canActivate &&
            (venue.status === VenueStatus.Pending ||
              venue.status === VenueStatus.Closed) && (
              <Tooltip
                title={
                  serviceCount === 0
                    ? 'A venue cannot be activated without at least one service'
                    : undefined
                }
              >
                <Button
                  type="primary"
                  loading={isActivating}
                  disabled={serviceCount === 0}
                  onClick={() => activateVenue(venue.id)}
                >
                  {venue.status === VenueStatus.Closed ? 'Reopen' : 'Activate'}
                </Button>
              </Tooltip>
            )}
          {canClose && venue.status === VenueStatus.Active && (
            <Button danger onClick={() => setCloseOpen(true)}>
              Close venue
            </Button>
          )}
          {canDisable &&
            (venue.status === VenueStatus.Pending ||
              venue.status === VenueStatus.Active) && (
              <Button
                danger
                loading={isDisabling}
                onClick={() => disableVenue(venue.id)}
              >
                Disable
              </Button>
            )}
          {canEnable && venue.status === VenueStatus.Disabled && (
            <Button
              type="primary"
              loading={isEnabling}
              onClick={() => enableVenue(venue.id)}
            >
              Enable
            </Button>
          )}
        </Space>
      </Card>

      <Modal
        title="Close venue"
        open={closeOpen}
        onCancel={closeCloseModal}
        okText="Close venue"
        okButtonProps={{
          danger: true,
          disabled: confirmName !== venue.name,
          loading: isClosing,
        }}
        onOk={() => closeVenue(venue.id)}
      >
        <Text>
          The venue will stop accepting new activity. Nothing is deleted —
          reopen it any time from this page. Type{' '}
          <Text strong>{venue.name}</Text> to confirm.
        </Text>
        <Input
          value={confirmName}
          onChange={(e) => setConfirmName(e.target.value)}
          placeholder={venue.name}
          style={{ marginTop: 12 }}
        />
      </Modal>
    </>
  );
}
