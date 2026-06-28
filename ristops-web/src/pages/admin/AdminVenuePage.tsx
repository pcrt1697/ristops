import { useState } from 'react';
import { Avatar, Card, Spin, theme, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import RequirePermission from '../../components/routing/RequirePermission.tsx';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import CreateVenueModal from '../../components/venue/CreateVenueModal.tsx';

const { Meta } = Card;

function CreateVenueCard() {
  const { token } = theme.useToken();
  const [modalOpen, setModalOpen] = useState(false);
  const { isAllowed: canAddVenues, isLoading } = useCan(
    { type: ResourceType.App, id: '*' },
    'venue:add',
  );

  if (isLoading) return <Spin fullscreen />;
  const onClick = canAddVenues ? () => setModalOpen(true) : undefined;
  const iconColor = canAddVenues ? token.colorPrimary : token.colorTextDisabled;
  return (
    <>
      <Card
        hoverable={canAddVenues}
        onClick={onClick}
        style={canAddVenues ? undefined : { borderColor: token.colorError }}
      >
        <Meta
          avatar={
            <Avatar
              icon={<PlusOutlined />}
              style={{ backgroundColor: iconColor }}
            />
          }
          title="Create Venue"
          description={
            canAddVenues ? (
              'Start setup procedure to create a new Venue'
            ) : (
              <Typography.Text type="danger">
                You don&apos;t have permission to create venues
              </Typography.Text>
            )
          }
        />
      </Card>
      <CreateVenueModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}

export default function AdminVenuePage() {
  return (
    <RequirePermission
      resource={{ type: ResourceType.App, id: '*' }}
      permissions={['venue:list']}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'start',
          alignItems: 'center',
        }}
      >
        <CreateVenueCard />
      </div>
    </RequirePermission>
  );
}
