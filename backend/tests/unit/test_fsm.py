"""Exhaustive tests for the Finite State Machine (FSM).

TDD test suite verifying all 25 state transition pairs and domain exception semantics.
"""

import pytest

from app.domain.exceptions import TransitionNotAllowedError, UnknownStatusError
from app.domain.fsm import (
    ALLOWED,
    Status,
    allowed_from,
    assert_transition,
    validate_status,
)

ALL_STATUSES = [
    Status.CREATED,
    Status.IN_REVIEW,
    Status.IN_PROGRESS,
    Status.PAUSED,
    Status.DONE,
]

EXPECTED_ALLOWED: dict[Status, set[Status]] = {
    Status.CREATED: {Status.IN_REVIEW},
    Status.IN_REVIEW: {Status.IN_PROGRESS, Status.PAUSED},
    Status.IN_PROGRESS: {Status.DONE, Status.PAUSED},
    Status.PAUSED: {Status.IN_REVIEW, Status.IN_PROGRESS},
    Status.DONE: set(),
}


def test_fsm_allowed_map_matches_specification():
    """Verify that every status in ALLOWED maps to the exact specification."""
    for current_status in ALL_STATUSES:
        assert current_status in ALLOWED
        assert set(ALLOWED[current_status]) == EXPECTED_ALLOWED[current_status]


def test_allowed_from_helper():
    """Verify allowed_from returns the expected frozenset of target statuses."""
    assert allowed_from(Status.CREATED) == frozenset({Status.IN_REVIEW})
    assert allowed_from(Status.IN_REVIEW) == frozenset({Status.IN_PROGRESS, Status.PAUSED})
    assert allowed_from(Status.IN_PROGRESS) == frozenset({Status.DONE, Status.PAUSED})
    assert allowed_from(Status.PAUSED) == frozenset({Status.IN_REVIEW, Status.IN_PROGRESS})
    assert allowed_from(Status.DONE) == frozenset()


@pytest.mark.parametrize(
    "current,target",
    [
        (Status.CREATED, Status.IN_REVIEW),
        (Status.IN_REVIEW, Status.IN_PROGRESS),
        (Status.IN_REVIEW, Status.PAUSED),
        (Status.IN_PROGRESS, Status.DONE),
        (Status.IN_PROGRESS, Status.PAUSED),
        (Status.PAUSED, Status.IN_PROGRESS),
        (Status.PAUSED, Status.IN_REVIEW),
    ],
)
def test_valid_transitions_succeed(current: Status, target: Status):
    """Assert valid transitions do not raise any exception."""
    assert_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        # From CREATED
        (Status.CREATED, Status.CREATED),
        (Status.CREATED, Status.IN_PROGRESS),
        (Status.CREATED, Status.PAUSED),
        (Status.CREATED, Status.DONE),
        # From IN_REVIEW
        (Status.IN_REVIEW, Status.CREATED),
        (Status.IN_REVIEW, Status.IN_REVIEW),
        (Status.IN_REVIEW, Status.DONE),
        # From IN_PROGRESS
        (Status.IN_PROGRESS, Status.CREATED),
        (Status.IN_PROGRESS, Status.IN_REVIEW),
        (Status.IN_PROGRESS, Status.IN_PROGRESS),
        # From PAUSED (cannot go to done directly or to created)
        (Status.PAUSED, Status.CREATED),
        (Status.PAUSED, Status.PAUSED),
        (Status.PAUSED, Status.DONE),
        # From DONE (terminal, cannot transition anywhere)
        (Status.DONE, Status.CREATED),
        (Status.DONE, Status.IN_REVIEW),
        (Status.DONE, Status.IN_PROGRESS),
        (Status.DONE, Status.PAUSED),
        (Status.DONE, Status.DONE),
    ],
)
def test_invalid_transitions_raise_transition_not_allowed(current: Status, target: Status):
    """Assert all forbidden transitions raise TransitionNotAllowedError with full context."""
    with pytest.raises(TransitionNotAllowedError) as exc_info:
        assert_transition(current, target)

    err = exc_info.value
    assert err.current == current
    assert err.target == target
    assert err.allowed == sorted(ALLOWED[current])
    assert f"'{current}'" in str(err)
    assert f"'{target}'" in str(err)


def test_status_enum_values():
    """Verify string values for enum members match slugs."""
    assert Status.CREATED == "created"
    assert Status.IN_REVIEW == "in_review"
    assert Status.IN_PROGRESS == "in_progress"
    assert Status.PAUSED == "paused"
    assert Status.DONE == "done"


def test_validate_status_valid_slugs():
    """Verify validate_status correctly parses valid slug strings."""
    for s in ALL_STATUSES:
        assert validate_status(s.value) == s


def test_validate_status_invalid_slug():
    """Verify validate_status raises UnknownStatusError on unrecognized strings."""
    with pytest.raises(UnknownStatusError) as exc_info:
        validate_status("invalid_status_code")
    assert "invalid_status_code" in str(exc_info.value)
