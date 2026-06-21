import { ConfigProvider, Spin, Table, type TableProps } from 'antd';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import { renderAccessDeniedTableContent } from '../table/utils.tsx';

interface VenueListTableDataType {
  id: string;
  name: string;
  address: string;
  description: string;
  createdAt: string;
}

const columns: TableProps<VenueListTableDataType>['columns'] = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Address', dataIndex: 'address', key: 'address' },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Creation date', dataIndex: 'creationDate', key: 'creationDate' },
];

export default function VenueListTable() {
  const { isAllowed: canListVenues, isLoading } = useCan(
    { type: ResourceType.App, id: '*' },
    'venue~list',
  );

  if (isLoading) return <Spin fullscreen />;

  return (
    <ConfigProvider
      renderEmpty={canListVenues ? undefined : renderAccessDeniedTableContent}
    >
      <Table<VenueListTableDataType>
        style={{ paddingTop: 10 }}
        columns={columns}
        dataSource={[]}
      />
    </ConfigProvider>
  );
}
