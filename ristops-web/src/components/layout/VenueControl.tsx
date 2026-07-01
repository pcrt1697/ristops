import { useState } from 'react';
import { Avatar, Flex, theme, Typography } from 'antd';
import { DownOutlined, ShopOutlined } from '@ant-design/icons';
import { useCurrentVenue, useVenue } from '../../domain/venue/venue.hooks.ts';
import { initials } from '../../commons/utils.ts';
import VenueDrawer from './VenueDrawer.tsx';

const { Text } = Typography;

export default function VenueControl() {
  const [open, setOpen] = useState(false);
  const { token } = theme.useToken();
  const { currentVenueId } = useCurrentVenue();
  const { data } = useVenue(currentVenueId);
  const venue = data?.venue;

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
