"""Async client for EXFO CTP10 vector analyzer using Pymeasure."""

import asyncio
from dataclasses import dataclass

from app.core.types import Err, Ok, Result
from app.hardware.base import BaseHardwareClient


@dataclass
class MeasurementParameters:
    """EXFO measurement parameters."""

    start_wavelength_nm: float
    stop_wavelength_nm: float
    resolution_pm: float
    sweep_speed_nm_per_s: float
    laser_power_dbm: float


@dataclass
class MeasurementData:
    """EXFO measurement data."""

    wavelength_nm: list[float]
    s11_db: list[float]  # Reflection
    s21_db: list[float]  # Transmission


class ExfoCTP10Client(BaseHardwareClient):
    """Async client for EXFO CTP10 vector analyzer."""

    def __init__(self, base_url: str = "http://localhost:8002", timeout: float = 300.0):
        """
        Initialize EXFO CTP10 client.

        Args:
            base_url: Base URL of EXFO API
            timeout: Request timeout (long for measurements)
        """
        super().__init__(base_url, timeout)

    # ========================================================================
    # Configuration
    # ========================================================================

    async def set_measurement_parameters(
        self, params: MeasurementParameters
    ) -> Result[None, str]:
        """
        Configure measurement parameters.

        Args:
            params: Measurement parameters

        Returns:
            Result with None or error
        """
        result = await self._post(
            "/configure",
            json={
                "start_wavelength_nm": params.start_wavelength_nm,
                "stop_wavelength_nm": params.stop_wavelength_nm,
                "resolution_pm": params.resolution_pm,
                "sweep_speed_nm_per_s": params.sweep_speed_nm_per_s,
                "laser_power_dbm": params.laser_power_dbm,
            },
        )
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    async def get_measurement_parameters(
        self,
    ) -> Result[MeasurementParameters, str]:
        """
        Get current measurement parameters.

        Returns:
            Result with MeasurementParameters or error
        """
        result = await self._get("/configure")
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok(
            MeasurementParameters(
                start_wavelength_nm=data["start_wavelength_nm"],
                stop_wavelength_nm=data["stop_wavelength_nm"],
                resolution_pm=data["resolution_pm"],
                sweep_speed_nm_per_s=data["sweep_speed_nm_per_s"],
                laser_power_dbm=data["laser_power_dbm"],
            )
        )

    # ========================================================================
    # Calibration
    # ========================================================================

    async def calibrate(self, channels: list[str] | None = None) -> Result[None, str]:
        """
        Calibrate measurement channels.

        Args:
            channels: List of channels to calibrate (e.g., ["S11", "S21"])
                     If None, calibrates all active channels

        Returns:
            Result with None or error
        """
        if channels is None:
            channels = ["S11", "S21"]

        result = await self._post("/calibrate", json={"channels": channels})
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    async def create_reference(self, channel: str) -> Result[None, str]:
        """
        Create reference trace for channel.

        Args:
            channel: Channel name (e.g., "S21")

        Returns:
            Result with None or error
        """
        result = await self._post("/reference/create", json={"channel": channel})
        if result.is_err():
            return Err(result.error)
        return Ok(None)

    # ========================================================================
    # Measurement
    # ========================================================================

    async def measure(
        self, calibrate: bool = True, cancel_event: asyncio.Event | None = None
    ) -> Result[MeasurementData, str]:
        """
        Execute measurement sweep.

        This is a long-running operation (30-300s depending on sweep parameters).
        The function will block until completion.

        Args:
            calibrate: Whether to calibrate before measurement
            cancel_event: Optional cancellation event (not yet fully implemented)

        Returns:
            Result with MeasurementData or error
        """
        result = await self._post("/measure", json={"calibrate": calibrate})
        if result.is_err():
            return Err(result.error)

        data = result.unwrap()
        return Ok(
            MeasurementData(
                wavelength_nm=data["wavelength_nm"],
                s11_db=data["s11_db"],
                s21_db=data["s21_db"],
            )
        )

    async def get_live_trace(self) -> Result[MeasurementData, str]:
        """
        Get live (real-time) measurement trace without storage.

        Returns:
            Result with MeasurementData or error
        """
        result = await self._get("/live")
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok(
            MeasurementData(
                wavelength_nm=data["wavelength_nm"],
                s11_db=data["s11_db"],
                s21_db=data["s21_db"],
            )
        )

    async def get_power(self, channel: str = "S21") -> Result[float, str]:
        """
        Get optical power reading from channel.

        Args:
            channel: Channel name (e.g., "S21")

        Returns:
            Result with power in dBm or error
        """
        result = await self._get(f"/power/{channel}")
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok(data["power_dbm"])

    # ========================================================================
    # Status
    # ========================================================================

    async def is_measuring(self) -> Result[bool, str]:
        """
        Check if device is currently measuring.

        Returns:
            Result with True if measuring, False otherwise, or error
        """
        result = await self._get("/status")
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok(data["measuring"])

    async def get_error_queue(self) -> Result[list[str], str]:
        """
        Get SCPI error queue.

        Returns:
            Result with list of error messages or error
        """
        result = await self._get("/errors")
        if result.is_err():
            return result

        data = result.unwrap()
        return Ok(data["errors"])


# ============================================================================
# NOTE: EXFO CTP10 API Server Implementation
# ============================================================================
#
# The EXFO CTP10 API server needs to be implemented separately using Pymeasure.
# This client expects a FastAPI server exposing the following endpoints:
#
# GET  /health                  - Health check
# POST /configure               - Set measurement parameters
# GET  /configure               - Get measurement parameters
# POST /calibrate               - Calibrate channels
# POST /reference/create        - Create reference trace
# POST /measure                 - Execute measurement
# GET  /live                    - Get live trace
# GET  /power/{channel}         - Get power reading
# GET  /status                  - Get device status
# GET  /errors                  - Get error queue
#
# The server should wrap Pymeasure instrument driver commands and expose
# them via REST API following the same pattern as the Suruga Seiki API.
#
# Example Pymeasure integration:
#
# from pymeasure.adapters import VISAAdapter
# from pymeasure.instruments.exfo import EXFOCTP10  # Custom instrument class
#
# class ExfoAPI:
#     def __init__(self, address: str):
#         adapter = VISAAdapter(address)
#         self.instrument = EXFOCTP10(adapter)
#
#     def configure(self, params):
#         self.instrument.start_wavelength = params.start_wavelength_nm
#         self.instrument.stop_wavelength = params.stop_wavelength_nm
#         # ... etc
#
#     def measure(self):
#         self.instrument.init()
#         self.instrument.wait_for_completion()
#         wavelength = self.instrument.get_wavelength_array()
#         s21 = self.instrument.get_trace("S21")
#         s11 = self.instrument.get_trace("S11")
#         return {"wavelength_nm": wavelength, "s21_db": s21, "s11_db": s11}
#
# ============================================================================
