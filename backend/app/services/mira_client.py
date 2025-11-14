"""MIRA database client with OAuth2 authentication."""

import gzip
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.core.types import Err, Ok, Result

logger = logging.getLogger(__name__)


class MIRAClient:
    """
    Async client for MIRA database API.

    Features:
    - OAuth2 authentication with AWS Cognito
    - Automatic token refresh on expiry
    - Local file-based caching (/tmp)
    - GZIP image decompression
    - Retry logic on 401 errors
    """

    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str | None = None,
        scope: str | None = None,
    ):
        """
        Initialize MIRA client.

        Args:
            base_url: MIRA API base URL (default: from settings based on env)
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_url: OAuth2 token endpoint
            scope: OAuth2 scope
        """
        self.base_url = (base_url or settings.mira_base_url_for_env).rstrip("/")
        self.client_id = client_id or settings.MIRA_CLIENT_ID
        self.client_secret = client_secret or settings.MIRA_CLIENT_SECRET
        self.token_url = token_url or settings.MIRA_TOKEN_URL
        self.scope = scope or settings.MIRA_SCOPE

        self.access_token: str | None = None
        self.token_expires_at: float = 0

        # HTTP client with connection pooling
        self._client = httpx.AsyncClient(timeout=600.0)

        # Cache directory
        self._cache_dir = Path("/tmp/mira_cache")
        self._cache_dir.mkdir(exist_ok=True)

        logger.info(f"MIRA client initialized for {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

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

    async def _get_token(self) -> Result[str, str]:
        """
        Get OAuth2 access token from AWS Cognito.

        Returns:
            Result with access token or error message
        """
        try:
            payload = (
                f"grant_type=client_credentials&"
                f"client_id={self.client_id}&"
                f"client_secret={self.client_secret}&"
                f"scope={self.scope}"
            )

            response = await self._client.post(
                self.token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)

            # Set expiry time (with 5min buffer for proactive refresh)
            self.token_expires_at = time.time() + expires_in - 300

            logger.info("Successfully obtained MIRA access token")
            return Ok(access_token)

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to get access token: HTTP {e.response.status_code}"
            logger.error(f"{error_msg}: {e.response.text}")
            return Err(error_msg)
        except Exception as e:
            error_msg = f"Failed to get access token: {str(e)}"
            logger.error(error_msg)
            return Err(error_msg)

    async def _ensure_token(self) -> Result[str, str]:
        """
        Ensure we have a valid access token.

        Proactively refreshes token if it expires in < 5 minutes.

        Returns:
            Result with access token or error message
        """
        if self.access_token and time.time() < self.token_expires_at:
            return Ok(self.access_token)

        logger.info("Token expired or missing, refreshing...")
        result = await self._get_token()
        if result.is_ok():
            self.access_token = result.unwrap()
            return Ok(self.access_token)
        return result

    async def _request(
        self,
        method: str,
        path: str,
        retry_on_401: bool = True,
        **kwargs,
    ) -> Result[httpx.Response, str]:
        """
        Make authenticated HTTP request with automatic token refresh.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/api/v3/devices/combs/...")
            retry_on_401: Retry with new token on 401
            **kwargs: Additional httpx request parameters

        Returns:
            Result with response or error message
        """
        # Ensure we have a valid token
        token_result = await self._ensure_token()
        if token_result.is_err():
            return Err(token_result.unwrap_err())

        token = token_result.unwrap()

        # Add authorization header
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self._client.request(
                method, f"{self.base_url}{path}", headers=headers, **kwargs
            )

            # Retry on 401 with new token
            if response.status_code == 401 and retry_on_401:
                logger.warning("Got 401, refreshing token and retrying...")
                self.access_token = None  # Force token refresh
                token_result = await self._ensure_token()
                if token_result.is_err():
                    return Err(token_result.unwrap_err())

                token = token_result.unwrap()
                headers["Authorization"] = f"Bearer {token}"

                response = await self._client.request(
                    method, f"{self.base_url}{path}", headers=headers, **kwargs
                )

            response.raise_for_status()
            return Ok(response)

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.error(f"Request failed for {path}: {error_msg}")
            return Err(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Request failed for {path}: {error_msg}")
            return Err(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Request failed for {path}: {error_msg}")
            return Err(error_msg)

    async def get_order_info(self, order_id: int) -> Result[dict[str, Any], str]:
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

        result = await self._request(
            "GET", f"/api/v3/devices/combs/linear_measurement/orders/{order_id}"
        )

        if result.is_err():
            return Err(result.unwrap_err())

        response = result.unwrap()
        data = response.json()

        # Cache the result
        self._write_cache(cache_key, data)

        return Ok(data)

    async def get_device_picture(
        self, comb_placed_id: int
    ) -> Result[bytes, str]:
        """
        Get device picture (GZIP-compressed PNG).

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

        result = await self._request(
            "GET",
            "/api/v3/devices/combs/search/png",
            params={"comb_placed_id": comb_placed_id},
            timeout=100.0,
        )

        if result.is_err():
            return Err(result.unwrap_err())

        response = result.unwrap()
        data = response.content

        # Decompress if GZIP
        if data.startswith(b"\x1f\x8b\x08"):  # GZIP magic bytes
            try:
                decompressed = gzip.decompress(data)
                logger.debug(
                    f"Decompressed image: {len(data)} -> {len(decompressed)} bytes"
                )
                data = decompressed
            except Exception as e:
                logger.warning(f"Failed to decompress image: {e}")
                # Continue with original data

        # Cache the result
        self._write_cache(cache_key, data)

        return Ok(data)

    async def get_setups(self) -> Result[list[dict], str]:
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

        result = await self._request(
            "GET", "/api/v3/devices/combs/linear_measurement/calibration/setups"
        )

        if result.is_err():
            return Err(result.unwrap_err())

        response = result.unwrap()
        data = response.json()

        # Cache the result
        self._write_cache(cache_key, data)

        return Ok(data.get("setups", []))

    async def create_measurement(
        self,
        devices_set_connector_id: int,
        setup_id: int,
        software_id: int,
        probe_station_mode_id: int,
        measurer_email: str | None = None,
    ) -> Result[int, str]:
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
        measurer_email = measurer_email or settings.MIRA_MEASURER_EMAIL

        payload = {
            "devices_set_connector_id": devices_set_connector_id,
            "status": "in_progress",
            "start_date": str(datetime.now(timezone.utc).replace(tzinfo=None)),
            "measurer_email": measurer_email,
            "waveguide_current_id": 1,
            "resonators_currents_set_id": 1,
            "setup_id": setup_id,
            "software_id": software_id,
            "probe_station_mode_id": probe_station_mode_id,
        }

        logger.info(
            f"Creating measurement for dsc_id={devices_set_connector_id}, "
            f"setup_id={setup_id}"
        )

        result = await self._request(
            "POST",
            "/api/v3/devices/combs/linear_measurement/measurement/",
            json=payload,
        )

        if result.is_err():
            return Err(result.unwrap_err())

        response = result.unwrap()
        data = response.json()

        measurement_id = data.get("id")
        if not measurement_id:
            return Err("Response did not contain measurement ID")

        logger.info(f"Created measurement with ID={measurement_id}")
        return Ok(measurement_id)

    async def upload_measurement_data(
        self, measurement_id: int, csv_content: str
    ) -> Result[bool, str]:
        """
        Upload measurement CSV data to MIRA.

        Args:
            measurement_id: Measurement ID
            csv_content: CSV file content as string

        Returns:
            Result with success boolean or error message
        """
        logger.info(f"Uploading measurement data for measurement_id={measurement_id}")

        files = {"file": ("measurement_data.csv", csv_content, "text/csv")}

        result = await self._request(
            "POST",
            "/api/v3/devices/combs/linear_measurement/measurement/data",
            params={"measurement_id": measurement_id},
            files=files,
        )

        if result.is_err():
            return Err(result.unwrap_err())

        logger.info(f"Successfully uploaded data for measurement_id={measurement_id}")
        return Ok(True)

    async def update_measurement_status(
        self, measurement_id: int, status: str
    ) -> Result[bool, str]:
        """
        Update measurement status.

        Args:
            measurement_id: Measurement ID
            status: New status (in_progress, completed, failed, cancelled)

        Returns:
            Result with success boolean or error message
        """
        logger.info(f"Updating measurement {measurement_id} status to {status}")

        result = await self._request(
            "PUT",
            f"/api/v3/devices/combs/linear_measurement/measurement/status/{measurement_id}",
            params={"meas_status": status},
        )

        if result.is_err():
            return Err(result.unwrap_err())

        return Ok(True)

    async def update_measurement_completed_date(
        self, measurement_id: int, completed_date: str | None = None
    ) -> Result[bool, str]:
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

        result = await self._request(
            "PUT",
            f"/api/v3/devices/combs/linear_measurement/measurement/completed_data/{measurement_id}",
            params={"completed_date": completed_date},
        )

        if result.is_err():
            return Err(result.unwrap_err())

        return Ok(True)

    async def health_check(self) -> Result[bool, str]:
        """
        Check MIRA API connectivity.

        Returns:
            Result with success boolean or error message
        """
        try:
            # Try to get token
            token_result = await self._ensure_token()
            if token_result.is_err():
                return Err(f"Authentication failed: {token_result.unwrap_err()}")

            # Try a simple API call (get setups)
            result = await self.get_setups()
            if result.is_err():
                return Err(f"API call failed: {result.unwrap_err()}")

            return Ok(True)
        except Exception as e:
            return Err(f"Health check failed: {str(e)}")
