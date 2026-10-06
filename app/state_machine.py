from enum import Enum


class TrolleyState(str, Enum):
    IDLE = "idle"

    USER_LOGGED_IN = "user_logged_in"
    BASKET_ASSIGNED = "basket_assigned"

    SHOPPING = "shopping"

    ADD_REQUESTED = "add_requested"
    CAMERA_VERIFYING_ADD = "camera_verifying_add"
    SERVO_OPENING = "servo_opening"
    WAITING_FOR_ADD = "waiting_for_add"
    VERIFYING_ADD = "verifying_add"

    REMOVAL_REQUESTED = "removal_requested"
    CAMERA_VERIFYING_REMOVAL = "camera_verifying_removal"
    WAITING_FOR_REMOVAL = "waiting_for_removal"
    VERIFYING_REMOVAL = "verifying_removal"

    SERVO_CLOSING = "servo_closing"

    ERROR = "error"
    ATTENDANT_REQUIRED = "attendant_required"


ALLOWED_TRANSITIONS = {
    TrolleyState.IDLE: {
        TrolleyState.USER_LOGGED_IN,
    },

    TrolleyState.USER_LOGGED_IN: {
        TrolleyState.BASKET_ASSIGNED,
        TrolleyState.IDLE,
    },

    TrolleyState.BASKET_ASSIGNED: {
        TrolleyState.SHOPPING,
        TrolleyState.IDLE,
    },

    TrolleyState.SHOPPING: {
        TrolleyState.ADD_REQUESTED,
        TrolleyState.REMOVAL_REQUESTED,
        TrolleyState.IDLE,
    },

    TrolleyState.ADD_REQUESTED: {
        TrolleyState.CAMERA_VERIFYING_ADD,
        TrolleyState.ERROR,
    },

    TrolleyState.CAMERA_VERIFYING_ADD: {
        TrolleyState.SERVO_OPENING,
        TrolleyState.ERROR,
    },

    TrolleyState.SERVO_OPENING: {
        TrolleyState.WAITING_FOR_ADD,
        TrolleyState.WAITING_FOR_REMOVAL,
        TrolleyState.ERROR,
    },

    TrolleyState.WAITING_FOR_ADD: {
        TrolleyState.VERIFYING_ADD,
        TrolleyState.ERROR,
    },

    TrolleyState.VERIFYING_ADD: {
        TrolleyState.SERVO_CLOSING,
        TrolleyState.ERROR,
    },

    TrolleyState.REMOVAL_REQUESTED: {
        TrolleyState.CAMERA_VERIFYING_REMOVAL,
        TrolleyState.ERROR,
    },

    TrolleyState.CAMERA_VERIFYING_REMOVAL: {
        TrolleyState.SERVO_OPENING,
        TrolleyState.ERROR,
    },

    TrolleyState.WAITING_FOR_REMOVAL: {
        TrolleyState.VERIFYING_REMOVAL,
        TrolleyState.ERROR,
    },

    TrolleyState.VERIFYING_REMOVAL: {
        TrolleyState.SERVO_CLOSING,
        TrolleyState.ERROR,
    },

    TrolleyState.SERVO_CLOSING: {
        TrolleyState.SHOPPING,
        TrolleyState.ERROR,
    },

    TrolleyState.ERROR: {
        TrolleyState.ADD_REQUESTED,
        TrolleyState.REMOVAL_REQUESTED,
        TrolleyState.ATTENDANT_REQUIRED,
    },

    TrolleyState.ATTENDANT_REQUIRED: {
        TrolleyState.SHOPPING,
        TrolleyState.IDLE,
    },
}


def can_transition(
    current_state: TrolleyState,
    next_state: TrolleyState,
) -> bool:
    return next_state in ALLOWED_TRANSITIONS.get(
        current_state,
        set(),
    )


def transition(
    current_state: TrolleyState,
    next_state: TrolleyState,
) -> TrolleyState:

    if not can_transition(current_state, next_state):
        raise ValueError(
            f"Invalid trolley state transition: "
            f"{current_state.value} -> {next_state.value}"
        )

    return next_state