"""Global measurement manager for coordinating measurement runs."""

import asyncio
from typing import Any

from fastapi import WebSocket

from app.core.state_machine import MeasurementState
from app.core.types import ProgressEvent
from app.services.controller import MeasurementConfig, MeasurementController


class WebSocketManager:
    """Manages WebSocket connections for progress broadcasting."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Add a WebSocket connection."""
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


class MeasurementManager:
    """
    Global singleton managing measurement controller lifecycle.

    Coordinates measurement runs, WebSocket broadcasting, and state queries.
    """

    def __init__(self):
        """Initialize measurement manager."""
        self.controller: MeasurementController | None = None
        self.task: asyncio.Task | None = None
        self.websocket_manager = WebSocketManager()

    def start(self, config: MeasurementConfig):
        """
        Start a new measurement run.

        Args:
            config: Measurement configuration

        Raises:
            RuntimeError: If a measurement is already running
        """
        if self.is_active():
            raise RuntimeError("A measurement is already running")

        self.controller = MeasurementController(config)
        self.task = asyncio.create_task(self._run_with_broadcasting())

    async def _run_with_broadcasting(self):
        """Run measurement controller and broadcast progress events."""
        if self.controller is None:
            return

        try:
            async for event in self.controller.run():
                # Broadcast event to WebSocket clients
                await self.websocket_manager.broadcast(self._event_to_dict(event))
        except Exception as e:
            # Broadcast error
            await self.websocket_manager.broadcast(
                {"event_type": "error", "error": str(e), "timestamp": 0.0}
            )

    def pause(self):
        """Pause the current measurement."""
        if self.controller:
            self.controller.pause()

    def resume(self):
        """Resume the current measurement."""
        if self.controller:
            self.controller.resume()

    async def cancel(self):
        """Cancel the current measurement."""
        if self.controller:
            self.controller.cancel()
            # Wait for task to complete
            if self.task:
                try:
                    await asyncio.wait_for(self.task, timeout=10.0)
                except asyncio.TimeoutError:
                    self.task.cancel()

    def is_active(self) -> bool:
        """Check if a measurement is currently active."""
        return self.controller is not None and (
            self.task is not None and not self.task.done()
        )

    def get_state(self) -> MeasurementState:
        """
        Get current measurement state.

        Returns:
            Current measurement state, or initial idle state if no measurement
        """
        if self.controller:
            return self.controller.get_state()
        else:
            from app.core.state_machine import MeasurementStateMachine

            return MeasurementStateMachine.initial_state()

    async def connect_websocket(self, websocket: WebSocket):
        """Connect a WebSocket client."""
        await self.websocket_manager.connect(websocket)

    def disconnect_websocket(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.websocket_manager.disconnect(websocket)

    @staticmethod
    def _event_to_dict(event: ProgressEvent) -> dict[str, Any]:
        """Convert ProgressEvent to dict for JSON serialization."""
        # Use dataclass __dict__ but handle special cases
        event_dict = {
            "event_type": event.event_type,
            "timestamp": event.timestamp,
        }

        # Add all fields except base class fields
        for field, value in event.__dict__.items():
            if field not in ("event_type", "timestamp"):
                event_dict[field] = value

        return event_dict


# ============================================================================
# Global Singleton
# ============================================================================

_measurement_manager: MeasurementManager | None = None


def get_measurement_manager() -> MeasurementManager:
    """Get global measurement manager instance."""
    global _measurement_manager
    if _measurement_manager is None:
        _measurement_manager = MeasurementManager()
    return _measurement_manager
