"""Measurement controller - orchestrates measurement workflow."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from app.core.state_machine import (
    CompleteDevice,
    MeasurementState,
    MeasurementStateMachine,
    StartDevice,
    StartMeasurement,
    UpdateOperation,
)
from app.core.types import (
    DeviceCompleted,
    DeviceMoving,
    DeviceSkipped,
    DeviceStarted,
    ErrorOccurred,
    MeasurementCancelled,
    MeasurementCompleted,
    MeasurementFailed,
    MeasurementOperation,
    MeasurementPaused,
    MeasurementResumed,
    MeasurementStarted,
    ProgressEvent,
)
from app.hardware.exfo_ctp10 import ExfoCTP10Client
from app.hardware.suruga_seiki import SurugaSeikiClient


@dataclass
class DeviceInfo:
    """Device information from chip design."""

    index: int
    name: str
    devices_set_connector_id: int
    input_port_position_y_um: float
    output_port_position_y_um: float


@dataclass
class MeasurementConfig:
    """Configuration for measurement run."""

    order_id: str
    devices: list[DeviceInfo]
    suruga_base_url: str
    exfo_base_url: str
    power_threshold_db: float = 1.5
    devices_between_alignments: int = 5
    perform_periodic_alignment: bool = True


class MeasurementController:
    """
    Async measurement controller with pause/cancel/resume support.

    This replaces the monolithic 992-line `__enter__` method with a clean,
    observable, controllable async generator pattern.
    """

    def __init__(self, config: MeasurementConfig):
        """
        Initialize measurement controller.

        Args:
            config: Measurement configuration
        """
        self.config = config
        self.state_machine = MeasurementStateMachine()
        self.state = self.state_machine.initial_state()

        # Control events
        self._pause_event = asyncio.Event()
        self._resume_event = asyncio.Event()
        self._cancel_event = asyncio.Event()

        # Hardware clients
        self.suruga: SurugaSeikiClient | None = None
        self.exfo: ExfoCTP10Client | None = None

        # Tracking
        self.alignment_counter = 0
        self.reference_power_left: float | None = None
        self.reference_power_right: float | None = None

    # ========================================================================
    # Main Orchestration
    # ========================================================================

    async def run(self) -> AsyncIterator[ProgressEvent]:
        """
        Execute measurement sequence, yielding progress events.

        This is an async generator that yields ProgressEvent instances
        as the measurement progresses. It can be paused, resumed, or
        cancelled via the control methods.

        Usage:
            controller = MeasurementController(config)
            async for event in controller.run():
                print(f"Progress: {event}")

        Yields:
            ProgressEvent instances (DeviceStarted, AlignmentProgress, etc.)
        """
        try:
            # Initialize hardware connections
            yield MeasurementStarted.now(
                order_id=self.config.order_id,
                total_devices=len(self.config.devices),
            )

            async with SurugaSeikiClient(
                self.config.suruga_base_url
            ) as suruga, ExfoCTP10Client(self.config.exfo_base_url) as exfo:
                self.suruga = suruga
                self.exfo = exfo

                # Transition to CALIBRATING state
                result = self.state_machine.transition(
                    self.state,
                    StartMeasurement(
                        order_id=self.config.order_id,
                        total_devices=len(self.config.devices),
                    ),
                )
                if result.is_err():
                    yield MeasurementFailed.now(
                        error=result.error, device_index=None
                    )
                    return
                self.state = result.unwrap()

                # TODO: Phase 2 - Calibration workflow
                # async for event in self._calibration_workflow():
                #     yield event

                # TODO: Phase 2 - Chip angle calibration
                # async for event in self._chip_angle_calibration():
                #     yield event

                # Process each device
                for device in self.config.devices:
                    # Check cancellation
                    if self._cancel_event.is_set():
                        yield MeasurementCancelled.now(device_index=device.index)
                        return

                    # Check pause
                    if self._pause_event.is_set():
                        yield MeasurementPaused.now(device_index=device.index)
                        # Wait for resume
                        await self._resume_event.wait()
                        self._resume_event.clear()
                        yield MeasurementResumed.now(device_index=device.index)

                    # Process device
                    async for event in self._process_device(device):
                        yield event

                # Complete measurement
                yield MeasurementCompleted.now(
                    total_devices=len(self.config.devices),
                    successful_devices=self.state.successful_devices,
                    failed_devices=len(self.config.devices)
                    - self.state.successful_devices,
                    total_duration_seconds=self.state.duration_seconds or 0.0,
                )

        except Exception as e:
            yield MeasurementFailed.now(error=str(e), device_index=None)

    # ========================================================================
    # Device Processing
    # ========================================================================

    async def _process_device(self, device: DeviceInfo) -> AsyncIterator[ProgressEvent]:
        """
        Process a single device measurement.

        Args:
            device: Device information

        Yields:
            Progress events
        """
        # Start device
        yield DeviceStarted.now(
            device_index=device.index,
            device_name=device.name,
            total_devices=len(self.config.devices),
        )

        result = self.state_machine.transition(
            self.state, StartDevice(device_index=device.index)
        )
        if result.is_err():
            yield ErrorOccurred.now(
                error=result.error,
                device_index=device.index,
                operation="start_device",
            )
            yield DeviceSkipped.now(
                device_index=device.index,
                device_name=device.name,
                reason=result.error,
            )
            return
        self.state = result.unwrap()

        # Move to device position
        yield DeviceMoving.now(device_index=device.index, device_name=device.name)
        result = self.state_machine.transition(
            self.state,
            UpdateOperation(operation=MeasurementOperation.MOVING_TO_DEVICE.value),
        )
        if result.is_ok():
            self.state = result.unwrap()

        # TODO: Phase 2 - Movement logic with angle correction
        # async for event in self._move_to_device(device):
        #     yield event

        # TODO: Phase 2 - Contact checking
        # async for event in self._check_contacts(device):
        #     yield event

        # TODO: Phase 2 - Power checking and alignment decision
        # async for event in self._check_power_and_align(device):
        #     yield event

        # TODO: Phase 2 - Execute EXFO measurement
        # async for event in self._execute_measurement(device):
        #     yield event

        # Complete device
        result = self.state_machine.transition(self.state, CompleteDevice())
        if result.is_ok():
            self.state = result.unwrap()

        yield DeviceCompleted.now(device_index=device.index, device_name=device.name)
        self.alignment_counter += 1

    # ========================================================================
    # Control Methods
    # ========================================================================

    def pause(self):
        """Pause the measurement at the next checkpoint."""
        self._pause_event.set()

    def resume(self):
        """Resume a paused measurement."""
        self._resume_event.set()

    def cancel(self):
        """Cancel the measurement."""
        self._cancel_event.set()

    def get_state(self) -> MeasurementState:
        """Get current state snapshot."""
        return self.state

    # ========================================================================
    # Helper Methods (Placeholders for Phase 2)
    # ========================================================================

    async def _move_to_device(self, device: DeviceInfo) -> AsyncIterator[ProgressEvent]:
        """
        Move stages to device position with angle correction.

        TODO: Implement in Phase 2
        """
        # Placeholder for safe Z-axis movement with angle correction
        # This will replace the complex safe_z_axis_move() logic from legacy code
        yield ErrorOccurred.now(
            error="Movement not yet implemented",
            device_index=device.index,
            operation="move_to_device",
        )

    async def _check_contacts(
        self, device: DeviceInfo
    ) -> AsyncIterator[ProgressEvent]:
        """
        Check contact sensors and retract if triggered.

        TODO: Implement in Phase 2
        """
        # Placeholder for contact checking with retraction
        yield ErrorOccurred.now(
            error="Contact checking not yet implemented",
            device_index=device.index,
            operation="check_contacts",
        )

    async def _check_power_and_align(
        self, device: DeviceInfo
    ) -> AsyncIterator[ProgressEvent]:
        """
        Check optical power and decide if alignment needed.

        TODO: Implement in Phase 2
        """
        # Placeholder for power checking and alignment decision logic
        yield ErrorOccurred.now(
            error="Power checking not yet implemented",
            device_index=device.index,
            operation="check_power",
        )

    async def _execute_measurement(
        self, device: DeviceInfo
    ) -> AsyncIterator[ProgressEvent]:
        """
        Execute EXFO measurement and upload data.

        TODO: Implement in Phase 2
        """
        # Placeholder for measurement execution
        yield ErrorOccurred.now(
            error="Measurement not yet implemented",
            device_index=device.index,
            operation="execute_measurement",
        )

    async def _calibration_workflow(self) -> AsyncIterator[ProgressEvent]:
        """
        Execute EXFO calibration workflow.

        TODO: Implement in Phase 2
        """
        # Placeholder for calibration
        yield ErrorOccurred.now(
            error="Calibration not yet implemented",
            device_index=None,
            operation="calibration",
        )

    async def _chip_angle_calibration(self) -> AsyncIterator[ProgressEvent]:
        """
        Execute chip angle calibration workflow.

        TODO: Implement in Phase 2
        """
        # Placeholder for chip angle calibration
        yield ErrorOccurred.now(
            error="Chip angle calibration not yet implemented",
            device_index=None,
            operation="chip_angle_calibration",
        )
