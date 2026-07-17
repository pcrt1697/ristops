import { VenueStatus } from '../../services/graphql/graphql.ts';

export const statusTagColor: Record<VenueStatus, string> = {
  [VenueStatus.Pending]: 'gold',
  [VenueStatus.Active]: 'green',
  [VenueStatus.Disabled]: 'red',
  [VenueStatus.Closed]: 'default',
};
