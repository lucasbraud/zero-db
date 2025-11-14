"""
MIRA database client using Timofey's api-auth and api-abstraction packages.

This is a simplified version that wraps the existing packages instead of
reimplementing OAuth2 authentication from scratch.

IMPORTANT: Environment variable DBMS_ADDRESS must be set in main.py BEFORE this module is imported!
"""

import gzip
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import api_auth
import api_abstraction.combs.linear_measurements
from PIL import Image
from io import BytesIO

from app.core.config import settings
from app.core.types import Err, Ok, Result

logger = logging.getLogger(__name__)


class MIRAClient:
    """
    Async wrapper around Timofey's MIRA client libraries.

    Uses:
    - api_auth.AuthService for OAuth2 authentication
    - api_abstraction.combs.linear_measurements.CombsLinearMeasurements for MIRA API

    Features:
    - Automatic OAuth2 token management (handled by api_auth)
    - Local file-based caching (/tmp)
    - GZIP image decompression
    - Async-compatible methods
    """

    def __init__(
        self,
        user_email: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize MIRA client.

        Args:
            user_email: User email for MIRA API tracking (default: from settings)
            base_url: MIRA API base URL (default: from settings based on env)
        """
        self.user_email = user_email or str(settings.MIRA_MEASURER_EMAIL)
        self.base_url = (base_url or settings.mira_base_url_for_env).rstrip("/")

        # Initialize auth service (OAuth2 handled automatically)
        self._auth_service: api_auth.AuthService | None = None
        self._mira_client: api_abstraction.combs.linear_measurements.CombsLinearMeasurements | None = None

        # Cache directory
        self._cache_dir = Path("/tmp/mira_cache")
        self._cache_dir.mkdir(exist_ok=True)

        logger.info(f"MIRA client initialized for {self.base_url} (user: {self.user_email})")

    def _ensure_connected(self):
        """Ensure auth service and MIRA client are initialized."""
        if self._auth_service is None:
            # Create auth service (no parameters needed, uses environment variables)
            # DBMS_ADDRESS should already be set in main.py before module import
            self._auth_service = api_auth.AuthService()
            self._auth_service.__enter__()  # Start auth session

            self._mira_client = api_abstraction.combs.linear_measurements.CombsLinearMeasurements(
                auth_service=self._auth_service
            )
            logger.info(f"MIRA auth service and client initialized")

    async def close(self):
        """Close auth session."""
        if self._auth_service:
            self._auth_service.__exit__(None, None, None)
            self._auth_service = None
            self._mira_client = None
            logger.info("MIRA auth session closed")

    def _cache_key(self, key: str) -> str:
        """Generate cache filename from key."""
        return hashlib.md5(key.encode()).hexdigest()

    def _read_cache(self, key: str) -> dict | bytes | None:
        """Read from file cache."""
        cache_file = self._cache_dir / self._cache_key(key)
        if not cache_file.exists():
            return None

        try:
            # Check TTL
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime > settings.MIRA_CACHE_TTL_SECONDS:
                cache_file.unlink()
                return None

            # Read data
            data = cache_file.read_bytes()

            # Try to parse as JSON (for order_info), otherwise return bytes (images)
            try:
                return json.loads(data.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return data
        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            return None

    def _write_cache(self, key: str, data: dict | bytes):
        """Write to file cache."""
        try:
            cache_file = self._cache_dir / self._cache_key(key)

            if isinstance(data, dict):
                cache_file.write_text(json.dumps(data))
            else:
                cache_file.write_bytes(data)

            logger.debug(f"Cached {key}")
        except Exception as e:
            logger.warning(f"Failed to write cache for {key}: {e}")

    async def get_order_info(self, order_id: int) -> Result[dict[str, Any]]:
        """
        Get order information including devices and measurement parameters.

        Args:
            order_id: Order ID

        Returns:
            Result with order info dict or error message
        """
        cache_key = f"order_info_{order_id}"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached and isinstance(cached, dict):
            logger.debug(f"Cache hit for order {order_id}")
            return Ok(cached)

        logger.info(f"Fetching order info for order_id={order_id}")

        try:
            self._ensure_connected()

            # Call Timofey's client (synchronous)
            # Note: api-abstraction is synchronous, we wrap it in async context
            order_data = self._mira_client.get_order_info(order_id=order_id)

            # Cache the result
            self._write_cache(cache_key, order_data)

            return Ok(order_data)

        except Exception as e:
            error_msg = f"Failed to get order {order_id}: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def get_device_picture(
        self, comb_placed_id: int
    ) -> Result[bytes]:
        """
        Get device picture (GZIP-compressed PNG, auto-decompressed).

        Args:
            comb_placed_id: Comb placed ID

        Returns:
            Result with decompressed PNG bytes or error message
        """
        cache_key = f"device_picture_{comb_placed_id}"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached and isinstance(cached, bytes):
            logger.debug(f"Cache hit for device picture {comb_placed_id}")
            return Ok(cached)

        logger.info(f"Fetching device picture for comb_placed_id={comb_placed_id}")

        try:
            self._ensure_connected()

            # Call Timofey's client (returns bytes)
            image_bytes = self._mira_client.get_device_picture(
                comb_placed_id=comb_placed_id
            )

            # Decompress if GZIP
            if image_bytes and image_bytes.startswith(b"\x1f\x8b\x08"):  # GZIP magic bytes
                try:
                    decompressed = gzip.decompress(image_bytes)
                    logger.debug(
                        f"Decompressed image: {len(image_bytes)} -> {len(decompressed)} bytes"
                    )
                    image_bytes = decompressed
                except Exception as e:
                    logger.warning(f"Failed to decompress image: {e}")
                    # Continue with original data

            # Cache the result
            self._write_cache(cache_key, image_bytes)

            return Ok(image_bytes)

        except Exception as e:
            error_msg = f"Failed to get device picture {comb_placed_id}: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def get_setups(self) -> Result[list[dict]]:
        """
        Get available measurement setups.

        Returns:
            Result with list of setups or error message
        """
        cache_key = "measurement_setups"

        # Check cache
        cached = self._read_cache(cache_key)
        if cached and isinstance(cached, dict) and "setups" in cached:
            logger.debug("Cache hit for measurement setups")
            return Ok(cached["setups"])

        logger.info("Fetching measurement setups")

        try:
            self._ensure_connected()

            # Call Timofey's client
            data = self._mira_client.get_setups()

            # Cache the result
            self._write_cache(cache_key, data)

            return Ok(data.get("setups", []))

        except Exception as e:
            error_msg = f"Failed to get setups: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def create_measurement(
        self,
        devices_set_connector_id: int,
        setup_id: int,
        software_id: int,
        probe_station_mode_id: int,
        measurer_email: str | None = None,
    ) -> Result[int]:
        """
        Create measurement entry in MIRA.

        Args:
            devices_set_connector_id: Device set connector ID
            setup_id: Setup ID
            software_id: Software ID
            probe_station_mode_id: Probe station mode ID (2=C-band, 4=O-band)
            measurer_email: Measurer email (default: from settings)

        Returns:
            Result with measurement ID or error message
        """
        measurer_email = measurer_email or self.user_email

        logger.info(
            f"Creating measurement for dsc_id={devices_set_connector_id}, "
            f"setup_id={setup_id}"
        )

        try:
            self._ensure_connected()

            # Call Timofey's client
            measurement_id = self._mira_client.create_measurement(
                devices_set_connector_id=devices_set_connector_id,
                setup_id=setup_id,
                software_id=software_id,
                probe_station_mode_id=probe_station_mode_id,
            )

            logger.info(f"Created measurement with ID={measurement_id}")
            return Ok(measurement_id)

        except Exception as e:
            error_msg = f"Failed to create measurement: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def upload_measurement_data(
        self, measurement_id: int, csv_content: str
    ) -> Result[bool]:
        """
        Upload measurement CSV data to MIRA.

        Args:
            measurement_id: Measurement ID
            csv_content: CSV file content as string

        Returns:
            Result with success boolean or error message
        """
        logger.info(f"Uploading measurement data for measurement_id={measurement_id}")

        try:
            self._ensure_connected()

            # Prepare files dict for Timofey's client
            from io import StringIO
            csv_file = StringIO(csv_content)
            files = {"file": ("measurement_data.csv", csv_file, "text/csv")}

            # Call Timofey's client
            self._mira_client.create_measurement_data(
                measurement_id=measurement_id,
                files=files,
            )

            logger.info(f"Successfully uploaded data for measurement_id={measurement_id}")
            return Ok(True)

        except Exception as e:
            error_msg = f"Failed to upload measurement data: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def update_measurement_status(
        self, measurement_id: int, status: str
    ) -> Result[bool]:
        """
        Update measurement status.

        Args:
            measurement_id: Measurement ID
            status: New status (in_progress, completed, failed, cancelled)

        Returns:
            Result with success boolean or error message
        """
        logger.info(f"Updating measurement {measurement_id} status to {status}")

        try:
            self._ensure_connected()

            # Call Timofey's client
            self._mira_client.update_measurement_status(
                measurement_id=measurement_id,
                status=status,
            )

            return Ok(True)

        except Exception as e:
            error_msg = f"Failed to update measurement status: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def update_measurement_completed_date(
        self, measurement_id: int, completed_date: str | None = None
    ) -> Result[bool]:
        """
        Update measurement completion timestamp.

        Args:
            measurement_id: Measurement ID
            completed_date: ISO format datetime string (default: now)

        Returns:
            Result with success boolean or error message
        """
        if completed_date is None:
            completed_date = str(datetime.now(timezone.utc).replace(tzinfo=None))

        logger.info(f"Updating measurement {measurement_id} completed date")

        try:
            self._ensure_connected()

            # Call Timofey's client
            self._mira_client.update_measurement_completed_data(
                measurement_id=measurement_id,
                completed_date=completed_date,
            )

            return Ok(True)

        except Exception as e:
            error_msg = f"Failed to update completion date: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def health_check(self) -> Result[bool]:
        """
        Check MIRA API connectivity.

        Returns:
            Result with success boolean or error message
        """
        try:
            # Try to initialize connection
            self._ensure_connected()

            # Try a simple API call (get setups)
            result = await self.get_setups()
            if result.is_err():
                return Err(f"API call failed: {result.unwrap_err()}")

            return Ok(True)
        except Exception as e:
            return Err(f"Health check failed: {str(e)}")
