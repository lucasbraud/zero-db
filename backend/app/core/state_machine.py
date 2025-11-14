"""Measurement state machine with immutable state transitions."""

from dataclasses import dataclass, field, replace
from datetime import datetime

from app.core.types import Err, MeasurementStatus, Ok, Result


# ============================================================================
# Measurement State
# ============================================================================


@dataclass(frozen=True)
class MeasurementState:
    """Immutable measurement state snapshot."""

    status: MeasurementStatus
    order_id: str | None
    current_device_index: int
    total_devices: int
    current_operation: str | None
    power_readings: dict[int, dict[str, float]]  # device_index -> {stage -> power}
    calibrated_setup_id: int | None
    left_stage_angle: float | None
    right_stage_angle: float | None
    error: str | None
    started_at: float | None
    completed_at: float | None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

    @property
    def successful_devices(self) -> int:
        """Count of successfully measured devices."""
        return len([p for p in self.power_readings.values() if p])

    @property
    def duration_seconds(self) -> float | None:
        """Total duration in seconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.now().timestamp()
        return end_time - self.started_at

    @property
    def is_running(self) -> bool:
        """Check if measurement is actively running."""
        return self.status == MeasurementStatus.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if measurement is paused."""
        return self.status == MeasurementStatus.PAUSED

    @property
    def is_active(self) -> bool:
        """Check if measurement is running or paused."""
        return self.status in (MeasurementStatus.RUNNING, MeasurementStatus.PAUSED)

    @property
    def is_terminal(self) -> bool:
        """Check if measurement is in terminal state."""
        return self.status in (
            MeasurementStatus.COMPLETED,
            MeasurementStatus.FAILED,
            MeasurementStatus.CANCELLED,
        )


# ============================================================================
# State Machine Events
# ============================================================================


class MeasurementEvent:
    """Base class for state machine events."""

    pass


@dataclass
class StartMeasurement(MeasurementEvent):
    """Start a new measurement."""

    order_id: str
    total_devices: int


@dataclass
class CompleteCalibration(MeasurementEvent):
    """Calibration completed."""

    calibrated_setup_id: int


@dataclass
class CompleteChipAngleCalibration(MeasurementEvent):
    """Chip angle calibration completed."""

    left_stage_angle: float
    right_stage_angle: float


@dataclass
class StartDevice(MeasurementEvent):
    """Start processing a device."""

    device_index: int


@dataclass
class UpdateOperation(MeasurementEvent):
    """Update current operation."""

    operation: str


@dataclass
class RecordPower(MeasurementEvent):
    """Record power reading."""

    device_index: int
    stage: str
    power_dbm: float


@dataclass
class CompleteDevice(MeasurementEvent):
    """Device measurement completed."""

    pass


@dataclass
class PauseMeasurement(MeasurementEvent):
    """Pause measurement."""

    pass


@dataclass
class ResumeMeasurement(MeasurementEvent):
    """Resume measurement."""

    pass


@dataclass
class CancelMeasurement(MeasurementEvent):
    """Cancel measurement."""

    pass


@dataclass
class CompleteMeasurement(MeasurementEvent):
    """Measurement completed successfully."""

    pass


@dataclass
class FailMeasurement(MeasurementEvent):
    """Measurement failed."""

    error: str


# ============================================================================
# State Machine
# ============================================================================


class MeasurementStateMachine:
    """State machine for measurement workflow with immutable state transitions."""

    @staticmethod
    def initial_state() -> MeasurementState:
        """Create initial idle state."""
        return MeasurementState(
            status=MeasurementStatus.IDLE,
            order_id=None,
            current_device_index=0,
            total_devices=0,
            current_operation=None,
            power_readings={},
            calibrated_setup_id=None,
            left_stage_angle=None,
            right_stage_angle=None,
            error=None,
            started_at=None,
            completed_at=None,
        )

    @staticmethod
    def transition(
        state: MeasurementState, event: MeasurementEvent
    ) -> Result[MeasurementState, str]:
        """
        Apply event to state, returning new state or error.

        This is the core state transition function. All state changes
        go through here, ensuring valid transitions and immutability.
        """
        # Validate transition based on current state and event type
        if isinstance(event, StartMeasurement):
            if state.status != MeasurementStatus.IDLE:
                return Err(f"Cannot start measurement from {state.status} state")
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.CALIBRATING,
                    order_id=event.order_id,
                    total_devices=event.total_devices,
                    current_device_index=0,
                    power_readings={},
                    error=None,
                    started_at=datetime.now().timestamp(),
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, CompleteCalibration):
            if state.status != MeasurementStatus.CALIBRATING:
                return Err(f"Cannot complete calibration from {state.status} state")
            return Ok(
                replace(
                    state,
                    calibrated_setup_id=event.calibrated_setup_id,
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, CompleteChipAngleCalibration):
            if state.status != MeasurementStatus.CALIBRATING:
                return Err(
                    f"Cannot complete chip angle calibration from {state.status} state"
                )
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.RUNNING,
                    left_stage_angle=event.left_stage_angle,
                    right_stage_angle=event.right_stage_angle,
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, StartDevice):
            if state.status not in (
                MeasurementStatus.RUNNING,
                MeasurementStatus.CALIBRATING,
            ):
                return Err(f"Cannot start device from {state.status} state")
            new_state = replace(
                state,
                current_device_index=event.device_index,
                timestamp=datetime.now().timestamp(),
            )
            # Transition to RUNNING if still in CALIBRATING
            if state.status == MeasurementStatus.CALIBRATING:
                new_state = replace(new_state, status=MeasurementStatus.RUNNING)
            return Ok(new_state)

        elif isinstance(event, UpdateOperation):
            if state.status not in (
                MeasurementStatus.RUNNING,
                MeasurementStatus.CALIBRATING,
            ):
                return Err(f"Cannot update operation from {state.status} state")
            return Ok(
                replace(
                    state,
                    current_operation=event.operation,
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, RecordPower):
            # Can record power from any active state
            if not state.is_active:
                return Err(f"Cannot record power from {state.status} state")
            # Create new power_readings dict with updated value
            new_power_readings = dict(state.power_readings)
            if event.device_index not in new_power_readings:
                new_power_readings[event.device_index] = {}
            new_power_readings[event.device_index] = {
                **new_power_readings[event.device_index],
                event.stage: event.power_dbm,
            }
            return Ok(
                replace(
                    state,
                    power_readings=new_power_readings,
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, CompleteDevice):
            if state.status != MeasurementStatus.RUNNING:
                return Err(f"Cannot complete device from {state.status} state")
            return Ok(replace(state, timestamp=datetime.now().timestamp()))

        elif isinstance(event, PauseMeasurement):
            if state.status != MeasurementStatus.RUNNING:
                return Err(f"Cannot pause from {state.status} state")
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.PAUSED,
                    current_operation=None,
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, ResumeMeasurement):
            if state.status != MeasurementStatus.PAUSED:
                return Err(f"Cannot resume from {state.status} state")
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.RUNNING,
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, CancelMeasurement):
            if not state.is_active:
                return Err(f"Cannot cancel from {state.status} state")
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.CANCELLED,
                    current_operation=None,
                    completed_at=datetime.now().timestamp(),
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, CompleteMeasurement):
            if state.status != MeasurementStatus.RUNNING:
                return Err(f"Cannot complete from {state.status} state")
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.COMPLETED,
                    current_operation=None,
                    completed_at=datetime.now().timestamp(),
                    timestamp=datetime.now().timestamp(),
                )
            )

        elif isinstance(event, FailMeasurement):
            if state.is_terminal:
                return Err(f"Cannot fail from terminal {state.status} state")
            return Ok(
                replace(
                    state,
                    status=MeasurementStatus.FAILED,
                    error=event.error,
                    current_operation=None,
                    completed_at=datetime.now().timestamp(),
                    timestamp=datetime.now().timestamp(),
                )
            )

        else:
            return Err(f"Unknown event type: {type(event).__name__}")
