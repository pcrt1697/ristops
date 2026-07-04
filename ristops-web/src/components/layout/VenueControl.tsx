import { useEffect, useState } from 'react';
import { Avatar, Flex, theme, Typography } from 'antd';
import { DownOutlined, ShopOutlined } from '@ant-design/icons';
import { useCurrentVenue, useVenue } from '../../domain/venue/venue.hooks.ts';
import { initials } from '../../commons/utils.ts';
import type { ServiceError } from '../../services/common.ts';
import VenueDrawer from './VenueDrawer.tsx';

const { Text } = Typography;

export default function VenueControl() {
  const [open, setOpen] = useState(false);
  const { token } = theme.useToken();
  const { currentVenueId, setCurrentVenueId } = useCurrentVenue();
  const { data, error } = useVenue(currentVenueId);
  const venue = data?.venue;

  // Self-heal: a stored venue that no longer exists (e.g. after a reseed) clears itself.
  useEffect(() => {
    if (currentVenueId && (error as ServiceError | null)?.status === 404) {
      setCurrentVenueId(null);
    }
  }, [currentVenueId, error, setCurrentVenueId]);

  return (
    <>
      <Flex
        align="center"
        gap={8}
        role="button"
        onClick={() => setOpen(true)}
        style={{ cursor: 'pointer' }}
      >
        {currentVenueId && venue ? (
          <>
            <Avatar
              size="small"
              style={{ backgroundColor: token.colorPrimary }}
            >
              {initials(venue.name)}
            </Avatar>
            <Text strong>{venue.name}</Text>
          </>
        ) : (
          <>
            <Avatar
              size="small"
              icon={<ShopOutlined />}
              style={{
                backgroundColor: 'transparent',
                color: token.colorTextTertiary,
                border: `1px dashed ${token.colorBorder}`,
              }}
            />
            <Text type="secondary">Select venue</Text>
          </>
        )}
        <DownOutlined
          style={{ fontSize: 12, color: token.colorTextTertiary }}
        />
      </Flex>
      <VenueDrawer open={open} onClose={() => setOpen(false)} />
    </>
  );
}
