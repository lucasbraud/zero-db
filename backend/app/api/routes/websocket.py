"""WebSocket endpoint for real-time measurement progress."""

from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.services.measurement_manager import MeasurementManager, get_measurement_manager

router = APIRouter()


@router.websocket("/progress")
async def websocket_measurement_progress(
    websocket: WebSocket,
    manager: Annotated[MeasurementManager, Depends(get_measurement_manager)],
):
    """
    WebSocket endpoint for real-time measurement progress updates.

    Clients connect to this endpoint to receive live progress events
    as the measurement runs. Events are broadcast at ~1Hz or when
    significant events occur (device started, alignment completed, etc.).

    Usage:
        ws = new WebSocket('ws://localhost:8000/api/v1/ws/progress')
        ws.onmessage = (event) => {
            const progress = JSON.parse(event.data)
            console.log(progress.event_type, progress)
        }
    """
    await manager.connect_websocket(websocket)

    try:
        # Keep connection alive and listen for client messages
        # (though we don't expect any - this is broadcast only)
        while True:
            # Wait for any message from client (or disconnection)
            data = await websocket.receive_text()
            # Echo back if client sends anything (for debugging)
            await websocket.send_json(
                {"type": "echo", "message": f"Received: {data}"}
            )

    except WebSocketDisconnect:
        manager.disconnect_websocket(websocket)
