"""Finite State Machine (FSM) declarative implementation for requests.

Rules:
created -> in_review -> in_progress -> done
paused can be reached from in_review and in_progress.
From paused, can only return to in_review or in_progress.
done is a terminal state.
"""

from enum import StrEnum
from app.domain.exceptions import TransitionNotAllowedError, UnknownStatusError


class Status(StrEnum):
    CREATED = "created"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    DONE = "done"


ALLOWED: dict[Status, frozenset[Status]] = {
    Status.CREATED: frozenset({Status.IN_REVIEW}),
    Status.IN_REVIEW: frozenset({Status.IN_PROGRESS, Status.PAUSED}),
    Status.IN_PROGRESS: frozenset({Status.DONE, Status.PAUSED}),
    Status.PAUSED: frozenset({Status.IN_REVIEW, Status.IN_PROGRESS}),
    Status.DONE: frozenset(),  # Terminal state
}


def allowed_from(current: Status) -> frozenset[Status]:
    """Return the set of valid target statuses from the given status."""
    return ALLOWED.get(current, frozenset())


def assert_transition(current: Status, target: Status) -> None:
    """Validate transition and raise TransitionNotAllowedError if forbidden."""
    valid_targets = ALLOWED.get(current, frozenset())
    if target not in valid_targets:
        raise TransitionNotAllowedError(
            current=current.value,
            target=target.value,
            allowed=sorted([s.value for s in valid_targets]),
        )


def validate_status(code: str) -> Status:
    """Parse and validate a string status slug into a Status enum."""
    try:
        return Status(code)
    except ValueError:
        raise UnknownStatusError(code)
