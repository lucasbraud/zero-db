"""Type definitions for measurement control system.

NOTE: This file is temporarily simplified for initial testing.
The full implementation with all progress event types is in types.py.backup
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar


# Result type for error handling
T = TypeVar('T')


@dataclass
class Ok(Generic[T]):
    """Success result."""
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value


@dataclass
class Err:
    """Error result."""
    error: str

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self):
        raise ValueError(self.error)


Result = Ok[T] | Err


# Measurement State Machine
class MeasurementState(str, Enum):
    """States for measurement workflow."""
    IDLE = "idle"
    CALIBRATING = "calibrating"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MeasurementStatus:
    """Current status of a measurement run."""
    state: MeasurementState
    current_operation: str = ""
    current_device: int = 0
    total_devices: int = 0
    progress_percent: float = 0.0
    error_message: str = ""


class AlignmentPhase(str, Enum):
    """Phases of optical alignment."""
    FIELD_SEARCH = "field_search"
    PEAK_SEARCH_X = "peak_search_x"
    PEAK_SEARCH_Y = "peak_search_y"
    PEAK_SEARCH_Z = "peak_search_z"
    CONVERGENCE = "convergence"


# Progress Events
@dataclass(frozen=True)
class ProgressEvent:
    """Base class for measurement progress events."""
    timestamp: float
    event_type: str

    @classmethod
    def now(cls, **kwargs):
        """Create event with current timestamp."""
        return cls(timestamp=datetime.now().timestamp(), **kwargs)


# Simplified event types for initial testing
@dataclass(frozen=True)
class MeasurementStarted(ProgressEvent):
    """Measurement sequence started."""
    event_type: str = "measurement_started"


@dataclass(frozen=True)
class MeasurementCompleted(ProgressEvent):
    """Measurement sequence completed."""
    event_type: str = "measurement_completed"


@dataclass(frozen=True)
class ErrorOccurred(ProgressEvent):
    """Error occurred during measurement."""
    event_type: str = "error_occurred"
    error: str = ""
