import { useState } from 'react';
import {
  Button,
  Dropdown,
  Form,
  Input,
  Modal,
  TimePicker,
  Tooltip,
  type MenuProps,
} from 'antd';
import { MoreOutlined } from '@ant-design/icons';
import dayjs, { type Dayjs } from 'dayjs';
import { useCan } from '../../domain/auth/auth.hooks.ts';
import {
  useCancelReservation,
  useCheckInReservation,
  useConfirmReservation,
  useNoShowReservation,
  useRejectReservation,
  useWithdrawReservation,
} from '../../domain/reservation/reservation.hooks.ts';
import {
  ResourceType,
  ReservationStatus,
  type SearchReservationsQuery,
} from '../../services/graphql/graphql.ts';

type Reservation = SearchReservationsQuery['reservations']['items'][number];

type ActionKey =
  | 'confirm'
  | 'reject'
  | 'cancel'
  | 'check_in'
  | 'no_show'
  | 'withdraw';

interface ActionFormValues {
  notes?: string;
  arrivalTime?: Dayjs;
}

/**
 * Which actions make sense from a given status. There is no backend state machine yet (it is a
 * later task), so this is the frontend's own reading of the lifecycle: a pending booking is
 * accepted or declined, an accepted one is honored or withdrawn, and terminal states are done.
 */
const ACTIONS_BY_STATUS: Record<ReservationStatus, ActionKey[]> = {
  [ReservationStatus.Pending]: ['confirm', 'reject', 'cancel'],
  [ReservationStatus.Confirmed]: ['check_in', 'no_show', 'cancel', 'withdraw'],
  [ReservationStatus.CheckedIn]: [],
  [ReservationStatus.Rejected]: [],
  [ReservationStatus.Canceled]: [],
  [ReservationStatus.NoShow]: [],
  [ReservationStatus.Withdrawn]: [],
};

/**
 * What can still be done to a booking on a service that no longer runs that day, being deleted
 * or closed. Nothing is going to be served, so accepting it, declining it or seating the party
 * makes no sense; it can only be called off by the customer or given up by the venue.
 */
const UNAVAILABLE_SERVICE_ACTIONS: ActionKey[] = ['cancel', 'withdraw'];

const ACTION_LABEL: Record<ActionKey, string> = {
  confirm: 'Confirm',
  reject: 'Reject',
  cancel: 'Cancel',
  check_in: 'Check in',
  no_show: 'Mark as no-show',
  withdraw: 'Withdraw',
};

/**
 * What each action means. The three ways a booking can end without the party arriving read
 * alike from their names, so the wording is mostly about telling them apart: who called it off,
 * and whether the venue had accepted it first.
 */
const ACTION_DESCRIPTION: Record<ActionKey, string> = {
  confirm: 'Accept the booking. The table is held and the party is expected.',
  reject: 'Decline a booking the venue will not take. Only for one still awaiting an answer.',
  cancel: 'Record that the customer called the booking off.',
  check_in: 'The party has arrived. Records the time of arrival against the booking.',
  no_show: 'The party never arrived and the table was held for nothing.',
  withdraw:
    'Give up a booking the venue already accepted but can no longer honor — after a closure '
    + 'or a schedule change, for instance. Venue-initiated, unlike a cancel or a reject.',
};

/** Permission each action needs. Note the hyphens — they match the authz grants exactly. */
const ACTION_PERMISSION: Record<ActionKey, string> = {
  confirm: 'reservation:confirm',
  reject: 'reservation:reject',
  cancel: 'reservation:cancel',
  check_in: 'reservation:check-in',
  no_show: 'reservation:no-show',
  withdraw: 'reservation:withdraw',
};

export default function ReservationStatusActions({
  venueId,
  reservation,
  serviceUnavailable = false,
}: {
  venueId: string;
  reservation: Reservation;
  serviceUnavailable?: boolean;
}) {
  const [form] = Form.useForm<ActionFormValues>();
  const [pendingAction, setPendingAction] = useState<ActionKey>();

  const resource = { type: ResourceType.Venue, id: venueId };
  const { isAllowed: canConfirm } = useCan(resource, ACTION_PERMISSION.confirm);
  const { isAllowed: canReject } = useCan(resource, ACTION_PERMISSION.reject);
  const { isAllowed: canCancel } = useCan(resource, ACTION_PERMISSION.cancel);
  const { isAllowed: canCheckIn } = useCan(resource, ACTION_PERMISSION.check_in);
  const { isAllowed: canNoShow } = useCan(resource, ACTION_PERMISSION.no_show);
  const { isAllowed: canWithdraw } = useCan(resource, ACTION_PERMISSION.withdraw);
  const allowed: Record<ActionKey, boolean> = {
    confirm: canConfirm,
    reject: canReject,
    cancel: canCancel,
    check_in: canCheckIn,
    no_show: canNoShow,
    withdraw: canWithdraw,
  };

  const confirmReservation = useConfirmReservation();
  const rejectReservation = useRejectReservation();
  const cancelReservation = useCancelReservation();
  const checkInReservation = useCheckInReservation();
  const noShowReservation = useNoShowReservation();
  const withdrawReservation = useWithdrawReservation();

  const available = ACTIONS_BY_STATUS[reservation.status].filter(
    (action) =>
      allowed[action] &&
      (!serviceUnavailable || UNAVAILABLE_SERVICE_ACTIONS.includes(action)),
  );
  if (available.length === 0) return null;

  const items: MenuProps['items'] = available.map((action) => ({
    key: action,
    label: (
      <Tooltip title={ACTION_DESCRIPTION[action]} placement="left">
        <span>{ACTION_LABEL[action]}</span>
      </Tooltip>
    ),
    danger: action === 'reject' || action === 'no_show' || action === 'withdraw',
    onClick: () => {
      form.resetFields();
      setPendingAction(action);
    },
  }));

  const isPending =
    confirmReservation.isPending ||
    rejectReservation.isPending ||
    cancelReservation.isPending ||
    checkInReservation.isPending ||
    noShowReservation.isPending ||
    withdrawReservation.isPending;

  function apply(action: ActionKey, values: ActionFormValues) {
    const id = reservation.id;
    const notes = values.notes || null;
    switch (action) {
      case 'confirm':
        return confirmReservation.mutateAsync({ id, notes });
      case 'reject':
        return rejectReservation.mutateAsync({ id, notes });
      case 'cancel':
        return cancelReservation.mutateAsync({ id, notes });
      case 'no_show':
        return noShowReservation.mutateAsync({ id, notes });
      case 'withdraw':
        return withdrawReservation.mutateAsync({ id, notes });
      case 'check_in':
        return checkInReservation.mutateAsync({
          id,
          // Omitted means "now", resolved venue-side in the venue's own timezone.
          arrivalTime: values.arrivalTime
            ? values.arrivalTime.format('HH:mm:ss')
            : null,
          notes,
        });
    }
  }

  function handleOk() {
    if (!pendingAction) return;
    form
      .validateFields()
      .then(async (values) => {
        await apply(pendingAction, values);
        setPendingAction(undefined);
      })
      .catch(() => {
        // mutation errors are surfaced by the hook's toast
      });
  }

  return (
    <>
      <Dropdown menu={{ items }} trigger={['click']}>
        <Button type="text" icon={<MoreOutlined />} />
      </Dropdown>
      <Modal
        title={pendingAction ? ACTION_LABEL[pendingAction] : ''}
        open={!!pendingAction}
        onOk={handleOk}
        onCancel={() => setPendingAction(undefined)}
        confirmLoading={isPending}
        okText={pendingAction ? ACTION_LABEL[pendingAction] : 'OK'}
        okButtonProps={{
          danger:
            pendingAction === 'reject' ||
            pendingAction === 'no_show' ||
            pendingAction === 'withdraw',
        }}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {pendingAction === 'check_in' && (
            <Form.Item
              name="arrivalTime"
              label="Arrival time"
              extra="Leave empty to record the current time."
            >
              <TimePicker
                format="HH:mm"
                style={{ width: '100%' }}
                defaultOpenValue={dayjs()}
              />
            </Form.Item>
          )}
          <Form.Item
            name="notes"
            label="Notes"
            extra="Replaces any notes already on the reservation."
          >
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
