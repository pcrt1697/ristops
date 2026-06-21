import { useState } from 'react';
import { Button, Spin } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import RequirePermission from '../../components/routing/RequirePermission.tsx';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import CreateVenueModal from '../../components/venue/CreateVenueModal.tsx';
import VenueListTable from '../../components/venue/VenueListTable.tsx';

function CreateVenueButton() {
  const [modalOpen, setModalOpen] = useState(false);
  const { isAllowed: canAddVenues, isLoading } = useCan(
    { type: ResourceType.App, id: '*' },
    'venue~add',
  );

  if (isLoading) return <Spin fullscreen />;

  return (
    <>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        disabled={!canAddVenues}
        onClick={() => setModalOpen(true)}
      >
        Create venue
      </Button>
      <CreateVenueModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}

export default function AdminVenuePage() {
  return (
    <RequirePermission
      resource={{ type: ResourceType.App, id: '*' }}
      permissions={['venue~list']}
    >
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <CreateVenueButton />
      </div>
      <VenueListTable />
    </RequirePermission>
  );
}
