"""Measurement control API endpoints."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_active_superuser
from app.core.types import MeasurementStatus
from app.models import User
from app.services.controller import (
    DeviceInfo,
    MeasurementConfig,
    MeasurementController,
)
from app.services.measurement_manager import MeasurementManager, get_measurement_manager

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class StartMeasurementRequest(BaseModel):
    """Request to start measurement."""

    order_id: str
    suruga_base_url: str = "http://localhost:8001"
    exfo_base_url: str = "http://localhost:8002"
    power_threshold_db: float = 1.5
    devices_between_alignments: int = 5
    perform_periodic_alignment: bool = True


class StartMeasurementResponse(BaseModel):
    """Response for start measurement."""

    message: str
    order_id: str
    total_devices: int


class MeasurementStatusResponse(BaseModel):
    """Measurement status response."""

    status: MeasurementStatus
    order_id: str | None
    current_device_index: int
    total_devices: int
    successful_devices: int
    current_operation: str | None
    error: str | None
    started_at: float | None
    duration_seconds: float | None


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/start", response_model=StartMeasurementResponse)
async def start_measurement(
    request: StartMeasurementRequest,
    background_tasks: BackgroundTasks,
    manager: Annotated[MeasurementManager, Depends(get_measurement_manager)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    """
    Start a new measurement sequence.

    This endpoint spawns a background task that runs the measurement workflow.
    Progress updates are broadcast via WebSocket.
    """
    # TODO: Fetch device information from MIRA database using api-abstraction
    # For now, use mock data
    devices = [
        DeviceInfo(
            index=i,
            name=f"Device_{i}",
            devices_set_connector_id=1000 + i,
            input_port_position_y_um=100.0 * i,
            output_port_position_y_um=100.0 * i,
        )
        for i in range(3)  # Mock 3 devices
    ]

    config = MeasurementConfig(
        order_id=request.order_id,
        devices=devices,
        suruga_base_url=request.suruga_base_url,
        exfo_base_url=request.exfo_base_url,
        power_threshold_db=request.power_threshold_db,
        devices_between_alignments=request.devices_between_alignments,
        perform_periodic_alignment=request.perform_periodic_alignment,
    )

    try:
        manager.start(config)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return StartMeasurementResponse(
        message="Measurement started",
        order_id=request.order_id,
        total_devices=len(devices),
    )


@router.post("/pause", response_model=MessageResponse)
async def pause_measurement(
    manager: Annotated[MeasurementManager, Depends(get_measurement_manager)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    """Pause the current measurement."""
    if not manager.is_active():
        raise HTTPException(status_code=400, detail="No active measurement")

    manager.pause()
    return MessageResponse(message="Measurement pause requested")


@router.post("/resume", response_model=MessageResponse)
async def resume_measurement(
    manager: Annotated[MeasurementManager, Depends(get_measurement_manager)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    """Resume a paused measurement."""
    state = manager.get_state()
    if state.status != MeasurementStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Measurement is not paused")

    manager.resume()
    return MessageResponse(message="Measurement resumed")


@router.post("/cancel", response_model=MessageResponse)
async def cancel_measurement(
    manager: Annotated[MeasurementManager, Depends(get_measurement_manager)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
):
    """Cancel the current measurement."""
    if not manager.is_active():
        raise HTTPException(status_code=400, detail="No active measurement")

    await manager.cancel()
    return MessageResponse(message="Measurement cancelled")


@router.get("/status", response_model=MeasurementStatusResponse)
async def get_measurement_status(
    manager: Annotated[MeasurementManager, Depends(get_measurement_manager)],
):
    """Get current measurement status."""
    state = manager.get_state()

    return MeasurementStatusResponse(
        status=state.status,
        order_id=state.order_id,
        current_device_index=state.current_device_index,
        total_devices=state.total_devices,
        successful_devices=state.successful_devices,
        current_operation=state.current_operation,
        error=state.error,
        started_at=state.started_at,
        duration_seconds=state.duration_seconds,
    )
