"""Base hardware client with async HTTP operations."""

import asyncio
from typing import Any

import httpx

from app.core.types import Err, Ok, Result


class BaseHardwareClient:
    """Base class for async hardware clients."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize hardware client.

        Args:
            base_url: Base URL for the hardware API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._connected = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> Result[None, str]:
        """Establish connection to hardware API."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            )
            # Test connection with health check
            response = await self._client.get("/health", timeout=5.0)
            if response.status_code == 200:
                self._connected = True
                return Ok(None)
            else:
                return Err(
                    f"Health check failed with status {response.status_code}"
                )
        except httpx.ConnectError as e:
            return Err(f"Failed to connect to {self.base_url}: {str(e)}")
        except Exception as e:
            return Err(f"Connection error: {str(e)}")

    async def disconnect(self):
        """Close connection to hardware API."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._client is not None

    async def _get(
        self, endpoint: str, params: dict | None = None
    ) -> Result[dict[str, Any], str]:
        """
        Async GET request.

        Args:
            endpoint: API endpoint (e.g., "/status")
            params: Query parameters

        Returns:
            Result with JSON response or error message
        """
        if not self.is_connected:
            return Err("Client not connected")

        try:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPStatusError as e:
            return Err(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            return Err(f"Request failed: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error: {str(e)}")

    async def _post(
        self, endpoint: str, json: dict | None = None
    ) -> Result[dict[str, Any], str]:
        """
        Async POST request.

        Args:
            endpoint: API endpoint
            json: JSON request body

        Returns:
            Result with JSON response or error message
        """
        if not self.is_connected:
            return Err("Client not connected")

        try:
            response = await self._client.post(endpoint, json=json)
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPStatusError as e:
            return Err(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            return Err(f"Request failed: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error: {str(e)}")

    async def _delete(self, endpoint: str) -> Result[dict[str, Any], str]:
        """
        Async DELETE request.

        Args:
            endpoint: API endpoint

        Returns:
            Result with JSON response or error message
        """
        if not self.is_connected:
            return Err("Client not connected")

        try:
            response = await self._client.delete(endpoint)
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPStatusError as e:
            return Err(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            return Err(f"Request failed: {str(e)}")
        except Exception as e:
            return Err(f"Unexpected error: {str(e)}")

    async def wait_with_cancellation(
        self, delay: float, cancel_event: asyncio.Event
    ) -> bool:
        """
        Wait for a delay, checking cancellation event.

        Args:
            delay: Delay in seconds
            cancel_event: Event to check for cancellation

        Returns:
            True if completed normally, False if cancelled
        """
        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=delay)
            return False  # Cancelled
        except asyncio.TimeoutError:
            return True  # Completed normally
