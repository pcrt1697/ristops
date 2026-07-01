import { useState } from 'react';
import {
  Avatar,
  Button,
  Divider,
  Drawer,
  Flex,
  Input,
  Spin,
  theme,
  Typography,
} from 'antd';
import { HomeOutlined, SearchOutlined, ShopOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import {
  useCurrentVenue,
  useSearchVenues,
  useVenue,
} from '../../domain/venue/venue.hooks.ts';
import { useDebounced } from '../../commons/hooks.ts';
import { initials, orNull } from '../../commons/utils.ts';

const { Text } = Typography;

interface VenueDrawerProps {
  open: boolean;
  onClose: () => void;
}

function VenueRow({ name, onClick }: { name: string; onClick: () => void }) {
  return (
    <Button
      type="text"
      block
      onClick={onClick}
      style={{
        height: 'auto',
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-start',
        gap: 8,
      }}
    >
      <Avatar size="small">{initials(name)}</Avatar>
      <span
        style={{
          flex: 1,
          textAlign: 'left',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {name}
      </span>
    </Button>
  );
}

export default function VenueDrawer({ open, onClose }: VenueDrawerProps) {
  const { token } = theme.useToken();
  const navigate = useNavigate();
  const { currentVenueId, setCurrentVenueId } = useCurrentVenue();
  const [search, setSearch] = useState('');
  const debounced = useDebounced(search);

  const { data: currentData } = useVenue(open ? currentVenueId : null);
  const currentVenue = currentData?.venue;

  const { data, isLoading } = useSearchVenues(
    { name: orNull(debounced) },
    { page: 0, pageSize: 5 },
  );
  const venues = (data?.searchVenues.items ?? []).filter(
    (v) => v.id !== currentVenueId,
  );

  const selectVenue = (id: string) => {
    setCurrentVenueId(id);
    void navigate(`/venues/${id}`);
    onClose();
  };
  const goHome = () => {
    void navigate('/');
    onClose();
  };
  const goToCurrentVenue = () => {
    if (!currentVenueId) return;
    void navigate(`/venues/${currentVenueId}`);
    onClose();
  };

  const header =
    currentVenueId && currentVenue ? (
      <Flex
        align="center"
        gap={8}
        role="button"
        onClick={goToCurrentVenue}
        style={{ cursor: 'pointer' }}
      >
        <Avatar style={{ backgroundColor: token.colorPrimary }}>
          {initials(currentVenue.name)}
        </Avatar>
        <Flex vertical>
          <Text strong style={{ lineHeight: 1.2 }}>
            {currentVenue.name}
          </Text>
          <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.2 }}>
            Current venue
          </Text>
        </Flex>
      </Flex>
    ) : (
      <Flex align="center" gap={8}>
        <Avatar
          icon={<ShopOutlined />}
          style={{
            backgroundColor: 'transparent',
            color: token.colorTextTertiary,
            border: `1px dashed ${token.colorBorder}`,
          }}
        />
        <Text type="secondary">Select venue</Text>
      </Flex>
    );

  return (
    <Drawer
      open={open}
      onClose={onClose}
      placement="left"
      size={300}
      title={header}
      styles={{ body: { padding: 12 } }}
    >
      <Flex vertical gap={4}>
        <Button
          type="text"
          block
          icon={<HomeOutlined />}
          onClick={goHome}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-start',
            gap: 8,
          }}
        >
          Home
        </Button>
        <Divider style={{ margin: '8px 0' }} />

        <Input
          placeholder="Search venues"
          allowClear
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {isLoading ? (
          <Flex justify="center" style={{ padding: 16 }}>
            <Spin />
          </Flex>
        ) : (
          venues.map((v) => (
            <VenueRow
              key={v.id}
              name={v.name}
              onClick={() => selectVenue(v.id)}
            />
          ))
        )}
      </Flex>
    </Drawer>
  );
}
