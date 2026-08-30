import { useEffect, useRef, useState } from 'react';
import { DatePicker, Flex, Tooltip, Typography, theme } from 'antd';
import { ExclamationCircleFilled } from '@ant-design/icons';
import dayjs, { type Dayjs } from 'dayjs';
import { useReservationCalendar } from '../../domain/reservation/reservation.hooks.ts';
import type { ReservationCalendarQuery } from '../../services/graphql/graphql.ts';

const { Text } = Typography;

type CalendarDay = ReservationCalendarQuery['reservationCalendar'][number];

// Keyed by name because the initials repeat (Tue/Thu, Sat/Sun).
const WEEKDAYS = [
  { key: 'mon', label: 'M' },
  { key: 'tue', label: 'T' },
  { key: 'wed', label: 'W' },
  { key: 'thu', label: 'T' },
  { key: 'fri', label: 'F' },
  { key: 'sat', label: 'S' },
  { key: 'sun', label: 'S' },
];

// The window opens on the current month with this many months either side of it, and slides:
// reaching either edge loads the same number again in that direction.
const MONTHS_PER_SIDE = 5;
const EDGE_PX = 320;

interface ReservationCalendarProps {
  venueId: string;
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

/**
 * Continuously scrolling month calendar, in the manner of the macOS and Windows date pickers:
 * months run one after another in a single scroll surface, extended as either edge is reached,
 * so navigating a year away is a scroll rather than twelve clicks.
 *
 * Cells stay deliberately bare — a day number, and a warning only where a service is over
 * capacity. Occupancy per service lives in the day pane, where there is room to read it.
 */
export default function ReservationCalendar({
  venueId,
  selectedDate,
  onSelectDate,
}: ReservationCalendarProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const anchorRef = useRef<HTMLDivElement>(null);
  const [range, setRange] = useState({
    before: MONTHS_PER_SIDE,
    after: MONTHS_PER_SIDE,
  });

  // The month the list is built around: the selection on first render, else the current month.
  // Fixed for the component's lifetime, so picking a day inside the mounted range never rebuilds
  // (and re-scrolls) the list.
  const [anchorMonth] = useState(() =>
    (selectedDate ? dayjs(selectedDate) : dayjs()).startOf('month'),
  );

  // Bring the anchor month into view once the list is mounted.
  useEffect(() => {
    anchorRef.current?.scrollIntoView({ block: 'start' });
  }, []);

  const months: Dayjs[] = [];
  for (let i = -range.before; i <= range.after; i += 1) {
    months.push(anchorMonth.add(i, 'month'));
  }

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    if (el.scrollHeight - el.scrollTop - el.clientHeight < EDGE_PX) {
      setRange((prev) => ({ ...prev, after: prev.after + MONTHS_PER_SIDE }));
    }
    if (el.scrollTop < EDGE_PX) {
      // Prepending months shifts everything down; restore the scroll offset by the height that
      // was added, so the view stays put instead of jumping backwards in time.
      const before = el.scrollHeight;
      setRange((prev) => ({ ...prev, before: prev.before + MONTHS_PER_SIDE }));
      requestAnimationFrame(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop += scrollRef.current.scrollHeight - before;
        }
      });
    }
  }

  return (
    <Flex vertical gap={12} style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
      <DatePicker
        value={selectedDate ? dayjs(selectedDate) : null}
        onChange={(d) => d && onSelectDate(d.format('YYYY-MM-DD'))}
        allowClear={false}
        style={{ width: '100%' }}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)' }}>
        {WEEKDAYS.map(({ key, label }) => (
          <Text
            key={key}
            type="secondary"
            style={{ fontSize: 12, textAlign: 'center' }}
          >
            {label}
          </Text>
        ))}
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}
      >
        {months.map((month) => {
          const key = month.format('YYYY-MM');
          return (
            <MonthBlock
              key={key}
              ref={month.isSame(anchorMonth, 'month') ? anchorRef : undefined}
              venueId={venueId}
              month={month}
              selectedDate={selectedDate}
              onSelectDate={onSelectDate}
            />
          );
        })}
      </div>
    </Flex>
  );
}

interface MonthBlockProps {
  ref?: React.Ref<HTMLDivElement>;
  venueId: string;
  month: Dayjs;
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

/**
 * One month of the scrolling list. Its occupancy is fetched the first time it is scrolled near
 * the viewport, so mounting a couple of years of months costs one request per month actually
 * looked at.
 */
function MonthBlock({
  ref,
  venueId,
  month,
  selectedDate,
  onSelectDate,
}: MonthBlockProps) {
  const { token } = theme.useToken();
  const blockRef = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false);

  useEffect(() => {
    const el = blockRef.current;
    if (!el || seen) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setSeen(true);
      },
      { rootMargin: '200px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [seen]);

  const { data } = useReservationCalendar(
    venueId,
    month.startOf('month').format('YYYY-MM-DD'),
    month.endOf('month').format('YYYY-MM-DD'),
    seen,
  );
  const dayByDate = new Map((data ?? []).map((day) => [day.businessDate, day]));

  // Only this month's own days are rendered; the 1st is offset to its weekday column, the way a
  // continuously scrolling calendar reads.
  const leading = (month.startOf('month').day() + 6) % 7;
  const days: Dayjs[] = [];
  for (let d = 1; d <= month.daysInMonth(); d += 1) {
    days.push(month.date(d));
  }

  return (
    <div
      ref={(node) => {
        blockRef.current = node;
        if (typeof ref === 'function') ref(node);
        else if (ref) ref.current = node;
      }}
      style={{ marginBottom: 16 }}
    >
      <Text
        strong
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 1,
          display: 'block',
          padding: '4px 0',
          background: token.colorBgContainer,
        }}
      >
        {month.format('MMMM YYYY')}
      </Text>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)' }}>
        {Array.from({ length: leading }, (_, i) => (
          <div key={`lead-${month.format('YYYY-MM')}-${i}`} />
        ))}
        {days.map((day) => (
          <DayCell
            key={day.format('YYYY-MM-DD')}
            day={day}
            summary={dayByDate.get(day.format('YYYY-MM-DD'))}
            selectedDate={selectedDate}
            onSelectDate={onSelectDate}
          />
        ))}
      </div>
    </div>
  );
}

interface DayCellProps {
  day: Dayjs;
  summary?: CalendarDay;
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

function DayCell({ day, summary, selectedDate, onSelectDate }: DayCellProps) {
  const { token } = theme.useToken();
  const dateIso = day.format('YYYY-MM-DD');
  const isSelected = dateIso === selectedDate;
  const isToday = day.isSame(dayjs(), 'day');
  const isSelectable = !!summary;
  const overCapacity = summary?.services.filter((s) => s.overCapacity) ?? [];

  return (
    <div
      onClick={isSelectable ? () => onSelectDate(dateIso) : undefined}
      style={{
        position: 'relative',
        aspectRatio: '1',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: token.borderRadius,
        border: `1px solid ${isSelected ? token.colorPrimary : 'transparent'}`,
        background: isSelected ? token.colorPrimaryBg : undefined,
        cursor: isSelectable ? 'pointer' : 'default',
      }}
    >
      <Text
        type={isSelectable ? undefined : 'secondary'}
        strong={isSelected || isToday}
        underline={isToday}
        delete={summary?.closed}
      >
        {day.date()}
      </Text>
      {overCapacity.length > 0 && (
        <Tooltip
          title={
            <>
              {overCapacity.map((service) => (
                <div key={service.serviceId}>
                  {service.serviceName}: {service.peakBooked} booked / {service.capacity}{' '}
                  seats ({service.peakBooked - service.capacity} over)
                </div>
              ))}
            </>
          }
        >
          <ExclamationCircleFilled
            style={{
              position: 'absolute',
              top: 2,
              right: 2,
              fontSize: 10,
              color: token.colorError,
            }}
          />
        </Tooltip>
      )}
    </div>
  );
}
