"""Async client for Suruga Seiki probe station API."""

import asyncio
from typing import Any

from app.core.types import AlignmentPhase, Err, Ok, Result, StagePosition
from app.hardware.base import BaseHardwareClient


class SurugaSeikiClient(BaseHardwareClient):
    """Async client for Suruga Seiki EW51 probe station."""

    def __init__(self, base_url: str = "http://localhost:8001", timeout: float = 300.0):
        """
        Initialize Suruga Seiki client.

        Args:
            base_url: Base URL of probe station API
            timeout: Request timeout (long for alignments)
        """
        super().__init__(base_url, timeout)

    # ========================================================================
    # Connection and Status
    # ========================================================================

    async def get_all_positions(self) -> Result[list[StagePosition], str]:
        """
        Get positions of all 12 axes.

        Returns:
            Result with list of StagePosition or error
        """
        result = await self._get("/position/all")
        if result.is_err():
            return result

        positions_data = result.unwrap()
        positions = []
        for axis_data in positions_data:
            positions.append(
                StagePosition(
                    axis_number=axis_data["axis_number"],
                    position_um=axis_data["position_um"],
                    moving=axis_data["moving"],
                    servo_on=axis_data["servo_on"],
                )
            )
        return Ok(positions)

    async def get_power(self, stage: str) -> Result[float, str]:
        """
        Get power meter reading.

        Args:
            stage: "left" or "right"

        Returns:
            Result with power in dBm or error
        """
        channel = 1 if stage == "left" else 2
        result = await self._get(f"/io/power/{channel}")
        if result.is_err():
            return result

        power_data = result.unwrap()
        return Ok(power_data["power"])

    # ========================================================================
    # Servo Control
    # ========================================================================

    async def turn_on_servos_batch(
        self, axis_numbers: list[int]
    ) -> Result[None, str]:
        """
        Turn on servos for multiple axes.

        Args:
            axis_numbers: List of axis numbers to activate

        Returns:
            Result with None or error
        """
        result = await self._post(
            "/servo/turn_on_servos_batch", json={"axis_numbers": axis_numbers}
        )
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    async def wait_for_axes_ready(
        self, axis_numbers: list[int], timeout: float = 10.0
    ) -> Result[None, str]:
        """
        Wait for axes to be ready (servo on, not moving, no errors).

        Args:
            axis_numbers: List of axis numbers to wait for
            timeout: Maximum wait time in seconds

        Returns:
            Result with None or error
        """
        result = await self._post(
            "/servo/wait_for_axes_ready_batch",
            json={"axis_numbers": axis_numbers, "timeout": timeout},
        )
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    # ========================================================================
    # Movement
    # ========================================================================

    async def move_absolute(
        self, axis_number: int, position_um: float, speed_um_per_s: float
    ) -> Result[None, str]:
        """
        Move axis to absolute position.

        Args:
            axis_number: Axis number (1-12)
            position_um: Target position in micrometers
            speed_um_per_s: Movement speed

        Returns:
            Result with None or error
        """
        result = await self._post(
            "/motion/move_absolute",
            json={
                "axis_number": axis_number,
                "position_um": position_um,
                "speed_um_per_s": speed_um_per_s,
            },
        )
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    async def move_relative(
        self, axis_number: int, distance_um: float, speed_um_per_s: float
    ) -> Result[None, str]:
        """
        Move axis relative to current position.

        Args:
            axis_number: Axis number (1-12)
            distance_um: Distance to move in micrometers
            speed_um_per_s: Movement speed

        Returns:
            Result with None or error
        """
        result = await self._post(
            "/motion/move_relative",
            json={
                "axis_number": axis_number,
                "distance_um": distance_um,
                "speed_um_per_s": speed_um_per_s,
            },
        )
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    async def emergency_stop(self) -> Result[None, str]:
        """
        Emergency stop all axes.

        Returns:
            Result with None or error
        """
        result = await self._post("/motion/emergency_stop", json={})
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    # ========================================================================
    # I/O (Contact Sensors)
    # ========================================================================

    async def get_analog_input(self, channel: int) -> Result[float, str]:
        """
        Get analog input voltage (contact sensor).

        Args:
            channel: Channel number (1-4)

        Returns:
            Result with voltage or error
        """
        result = await self._get(f"/io/analog_input/{channel}")
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok(data["voltage"])

    async def set_digital_output(
        self, channel: int, value: bool
    ) -> Result[None, str]:
        """
        Set digital output (contact lock).

        Args:
            channel: Channel number
            value: True to lock, False to unlock

        Returns:
            Result with None or error
        """
        result = await self._post(
            "/io/set_digital_output", json={"channel": channel, "value": value}
        )
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    # ========================================================================
    # Optical Alignment
    # ========================================================================

    async def execute_flat_alignment(
        self, request: dict[str, Any], cancel_event: asyncio.Event | None = None
    ) -> Result[dict[str, Any], str]:
        """
        Execute 2D flat alignment (X-Y).

        This is a long-running operation (30+ seconds). The function will
        block until completion. Cancel via cancel_event is not currently
        supported by the hardware API.

        Args:
            request: Flat alignment request parameters
            cancel_event: Optional cancellation event (not yet implemented)

        Returns:
            Result with alignment response or error
        """
        # Note: Current hardware API doesn't support cancellation mid-alignment
        # This would require enhancement to the probe-flow API
        result = await self._post("/alignment/flat", json=request)
        if result.is_err():
            return Err(result.error)

        response = result.unwrap()
        return Ok(response)

    async def execute_focus_alignment(
        self, request: dict[str, Any], cancel_event: asyncio.Event | None = None
    ) -> Result[dict[str, Any], str]:
        """
        Execute 3D focus alignment (X-Y-Z).

        This is a long-running operation (60+ seconds). The function will
        block until completion. Cancel via cancel_event is not currently
        supported by the hardware API.

        Args:
            request: Focus alignment request parameters
            cancel_event: Optional cancellation event (not yet implemented)

        Returns:
            Result with alignment response or error
        """
        result = await self._post("/alignment/focus", json=request)
        if result.is_err():
            return Err(result.error)

        response = result.unwrap()
        return Ok(response)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def safe_z_retract_and_move(
        self,
        z_axis: int,
        x_axis: int,
        retract_distance_um: float,
        target_x_position_um: float,
        speed_um_per_s: float,
        cancel_event: asyncio.Event,
    ) -> Result[None, str]:
        """
        Safely retract Z axis, move X axis, then extend Z back.

        Args:
            z_axis: Z axis number
            x_axis: X axis number
            retract_distance_um: How far to retract Z
            target_x_position_um: Target X position
            speed_um_per_s: Movement speed
            cancel_event: Cancellation event

        Returns:
            Result with None or error
        """
        # Check cancellation
        if cancel_event.is_set():
            return Err("Operation cancelled")

        # Get current Z position
        result = await self._get(f"/position/{z_axis}")
        if result.is_err():
            return Err(f"Failed to get Z position: {result.error}")
        current_z = result.unwrap()["position_um"]

        # Retract Z
        retract_result = await self.move_relative(
            z_axis, -retract_distance_um, speed_um_per_s
        )
        if retract_result.is_err():
            return Err(f"Failed to retract Z: {retract_result.error}")

        # Wait for Z to settle
        await asyncio.sleep(0.2)

        # Check cancellation
        if cancel_event.is_set():
            return Err("Operation cancelled")

        # Move X to target
        move_result = await self.move_absolute(
            x_axis, target_x_position_um, speed_um_per_s
        )
        if move_result.is_err():
            return Err(f"Failed to move X: {move_result.error}")

        # Wait for X to settle
        await asyncio.sleep(0.2)

        # Check cancellation
        if cancel_event.is_set():
            return Err("Operation cancelled")

        # Extend Z back to original position
        extend_result = await self.move_absolute(z_axis, current_z, speed_um_per_s)
        if extend_result.is_err():
            return Err(f"Failed to extend Z: {extend_result.error}")

        # Wait for Z to settle
        await asyncio.sleep(0.2)

        return Ok(None)

    async def check_contact_and_retract(
        self,
        contact_channel: int,
        z_axis: int,
        threshold_voltage: float,
        retract_step_um: float,
        max_retract_steps: int,
        speed_um_per_s: float,
        cancel_event: asyncio.Event,
    ) -> Result[bool, str]:
        """
        Check contact sensor and retract Z if triggered.

        Args:
            contact_channel: Analog input channel for contact sensor
            z_axis: Z axis number
            threshold_voltage: Contact detection threshold (e.g., 0.01V)
            retract_step_um: Distance to retract per step (e.g., 1um)
            max_retract_steps: Maximum retraction steps (e.g., 30)
            speed_um_per_s: Retraction speed
            cancel_event: Cancellation event

        Returns:
            Result with True if contact detected, False otherwise, or error
        """
        voltage_result = await self.get_analog_input(contact_channel)
        if voltage_result.is_err():
            return Err(f"Failed to read contact sensor: {voltage_result.error}")

        voltage = voltage_result.unwrap()

        if voltage > threshold_voltage:
            # Contact detected, retract Z
            for step in range(max_retract_steps):
                if cancel_event.is_set():
                    return Err("Operation cancelled during contact retraction")

                retract_result = await self.move_relative(
                    z_axis, -retract_step_um, speed_um_per_s
                )
                if retract_result.is_err():
                    return Err(
                        f"Failed to retract Z at step {step}: {retract_result.error}"
                    )

                await asyncio.sleep(0.1)

                # Check if contact cleared
                voltage_result = await self.get_analog_input(contact_channel)
                if voltage_result.is_err():
                    return Err(
                        f"Failed to read contact sensor after retraction: {voltage_result.error}"
                    )

                voltage = voltage_result.unwrap()
                if voltage <= threshold_voltage:
                    return Ok(True)  # Contact cleared

            return Err(
                f"Contact persisted after {max_retract_steps} retraction steps"
            )

        return Ok(False)  # No contact
