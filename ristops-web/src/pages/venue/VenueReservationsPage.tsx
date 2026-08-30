import { useEffect } from 'react';
import { Result, theme } from 'antd';
import { useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { useSearchParamState } from '../../commons/hooks.ts';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import { useReservationCalendar } from '../../domain/reservation/reservation.hooks.ts';
import { ResourceType } from '../../services/graphql/graphql.ts';
import ReservationCalendar from '../../components/reservation/ReservationCalendar.tsx';
import ReservationDaySection from '../../components/reservation/ReservationDaySection.tsx';

const RAIL_WIDTH = 320;

export default function VenueReservationsPage() {
  const { venueId = '' } = useParams<{ venueId: string }>();
  const { token } = theme.useToken();
  const resource = { type: ResourceType.Venue, id: venueId };
  const { isAllowed: canList, isLoading: loadingPermissions } = useCan(
    resource,
    'reservation:list',
  );
  const { isAllowed: canBook } = useCan(resource, 'reservation:add');

  // The selected day lives in the URL so it is deep-linkable.
  const [selectedDate, setSelectedDate] = useSearchParamState('date');

  // Arriving without a date lands on today, written into the URL so the view is always
  // shareable. `useSearchParamState` replaces rather than pushes, so this adds no history entry
  // and the back button still leaves the page.
  useEffect(() => {
    if (!selectedDate) setSelectedDate(dayjs().format('YYYY-MM-DD'));
  }, [selectedDate, setSelectedDate]);

  // Render today straight away rather than waiting for the effect above to write it, so the
  // page never flashes an empty state on the way in.
  const date = selectedDate || dayjs().format('YYYY-MM-DD');

  // The day pane needs the selected day's occupancy. This asks for the month containing it,
  // which is the same query key the calendar's own month block uses — so the two share one
  // request rather than issuing a second.
  const { data } = useReservationCalendar(
    venueId,
    dayjs(date).startOf('month').format('YYYY-MM-DD'),
    dayjs(date).endOf('month').format('YYYY-MM-DD'),
  );

  if (loadingPermissions) return null;
  if (!canList) {
    return (
      <Result
        status="403"
        title="Not allowed"
        subTitle="You don't have permission to view this venue's reservations."
      />
    );
  }

  const selectedDay = (data ?? []).find((day) => day.businessDate === date);

  return (
    // `overflow: hidden` pins the page to exactly the height of the layout's Content, so the
    // page itself never scrolls — only the two columns do, each on its own.
    <div
      style={{
        display: 'flex',
        gap: 24,
        height: '100%',
        minHeight: 0,
        overflow: 'hidden',
        alignItems: 'stretch',
      }}
    >
      <div
        style={{
          flex: `0 0 ${RAIL_WIDTH}px`,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
          // Not a scroll container: the calendar scrolls its month list internally, so the date
          // picker and weekday header stay pinned at the top of the column.
          overflow: 'hidden',
          paddingRight: 16,
          borderRight: `1px solid ${token.colorSplit}`,
        }}
      >
        <ReservationCalendar
          venueId={venueId}
          selectedDate={date}
          onSelectDate={setSelectedDate}
        />
      </div>

      <div
        style={{
          flex: 1,
          minWidth: 0,
          minHeight: 0,
          overflowY: 'auto',
        }}
      >
        <ReservationDaySection
          venueId={venueId}
          date={date}
          day={selectedDay}
          canBook={canBook}
        />
      </div>
    </div>
  );
}
