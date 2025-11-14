"""API routes for MIRA order information."""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from PIL import Image
from io import BytesIO

from app.api.deps import CurrentUser, MIRAClientDep
from app.core.config import settings
from app.models import OrderBulkRequest, OrderInfoResponse, DeviceWithPicture

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/orders/health")
async def mira_health_check(
    current_user: CurrentUser,
    mira: MIRAClientDep,
) -> dict[str, Any]:
    """
    Check MIRA API connectivity.

    Returns:
        Health status

    Raises:
        HTTPException: If MIRA is unavailable
    """
    result = await mira.health_check()
    if result.is_err():
        raise HTTPException(
            status_code=503,
            detail=f"MIRA health check failed: {result.unwrap_err()}",
        )

    return {
        "status": "healthy",
        "mira_base_url": mira.base_url,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/orders/{order_id}", response_model=OrderInfoResponse)
async def get_order(
    order_id: int,
    mira: MIRAClientDep,
    # current_user: CurrentUser,  # Disabled for testing - enable in production
) -> OrderInfoResponse:
    """
    Get order information with device list.

    Args:
        order_id: Order ID
        mira: MIRA client instance

    Returns:
        Order information with devices and picture URLs

    Raises:
        HTTPException: If order not found or API error
    """
    logger.info(f"Anonymous user requesting order {order_id}")

    # Get order info from MIRA
    result = await mira.get_order_info(order_id)
    if result.is_err():
        logger.error(f"Failed to get order {order_id}: {result.unwrap_err()}")
        raise HTTPException(
            status_code=404,
            detail=f"Failed to get order information: {result.unwrap_err()}",
        )

    order_data = result.unwrap()

    # Transform devices to include picture URLs
    devices_with_pictures = []
    for device in order_data.get("devices", []):
        # Generate picture URL
        picture_url = (
            f"{settings.API_V1_STR}/orders/{order_id}/devices/"
            f"{device['comb_placed_id']}/picture"
        )

        device_with_picture = DeviceWithPicture(
            **device,
            picture_url=picture_url,
        )
        devices_with_pictures.append(device_with_picture)

    # Construct response
    response = OrderInfoResponse(
        order_id=order_data.get("order_id", order_id),
        order_name=order_data.get("order_name"),
        devices=devices_with_pictures,
        measurement_parameters=order_data.get("measurement_parameters"),
        calibrated_setup_id=order_data.get("calibrated_setup_id"),
    )

    return response


@router.post("/orders/bulk", response_model=list[OrderInfoResponse])
async def get_orders_bulk(
    request: OrderBulkRequest,
    current_user: CurrentUser,
    mira: MIRAClientDep,
) -> list[OrderInfoResponse]:
    """
    Get multiple orders (for multi-chip measurements).

    Maximum 4 orders per request.

    Args:
        request: Bulk order request with order IDs
        current_user: Authenticated user
        mira: MIRA client instance

    Returns:
        List of order information

    Raises:
        HTTPException: If any order not found or API error
    """
    logger.info(
        f"User {current_user.email} requesting {len(request.order_ids)} orders: "
        f"{request.order_ids}"
    )

    # Validate max orders
    if len(request.order_ids) > settings.MIRA_MAX_ORDERS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MIRA_MAX_ORDERS_PER_REQUEST} orders allowed per request",
        )

    # Fetch orders in parallel
    tasks = [mira.get_order_info(order_id) for order_id in request.order_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    responses = []
    errors = []

    for order_id, result in zip(request.order_ids, results):
        if isinstance(result, Exception):
            errors.append(f"Order {order_id}: {str(result)}")
            continue

        if result.is_err():
            errors.append(f"Order {order_id}: {result.unwrap_err()}")
            continue

        order_data = result.unwrap()

        # Transform devices to include picture URLs
        devices_with_pictures = []
        for device in order_data.get("devices", []):
            picture_url = (
                f"{settings.API_V1_STR}/orders/{order_id}/devices/"
                f"{device['comb_placed_id']}/picture"
            )

            device_with_picture = DeviceWithPicture(
                **device,
                picture_url=picture_url,
            )
            devices_with_pictures.append(device_with_picture)

        response = OrderInfoResponse(
            order_id=order_data.get("order_id", order_id),
            order_name=order_data.get("order_name"),
            devices=devices_with_pictures,
            measurement_parameters=order_data.get("measurement_parameters"),
            calibrated_setup_id=order_data.get("calibrated_setup_id"),
        )
        responses.append(response)

    # If any errors occurred, include them in the response
    if errors:
        logger.warning(f"Errors during bulk order fetch: {errors}")
        # Still return partial results if some succeeded
        if not responses:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to fetch orders: {'; '.join(errors)}",
            )

    return responses


@router.get("/orders/{order_id}/devices/{comb_placed_id}/picture")
async def get_device_picture(
    order_id: int,
    comb_placed_id: int,
    mira: MIRAClientDep,
    thumbnail: bool = False,
    # current_user: CurrentUser,  # Disabled for testing - enable in production
) -> Response:
    """
    Get device picture (PNG).

    Args:
        order_id: Order ID (for context/logging)
        comb_placed_id: Comb placed ID
        thumbnail: If True, return 256x256 thumbnail
        mira: MIRA client instance

    Returns:
        PNG image as bytes

    Raises:
        HTTPException: If image not found or API error
    """
    logger.info(
        f"Anonymous user requesting picture for device "
        f"{comb_placed_id} (order {order_id}, thumbnail={thumbnail})"
    )

    # Get device picture from MIRA
    result = await mira.get_device_picture(comb_placed_id)
    if result.is_err():
        logger.error(
            f"Failed to get picture for device {comb_placed_id}: "
            f"{result.unwrap_err()}"
        )
        raise HTTPException(
            status_code=404,
            detail=f"Failed to get device picture: {result.unwrap_err()}",
        )

    image_bytes = result.unwrap()

    # Generate thumbnail if requested
    if thumbnail:
        try:
            image = Image.open(BytesIO(image_bytes))
            image.thumbnail((256, 256), Image.Resampling.LANCZOS)

            # Save back to bytes
            output = BytesIO()
            image.save(output, format="PNG")
            image_bytes = output.getvalue()

            logger.debug(f"Generated thumbnail for device {comb_placed_id}")
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}, returning full image")
            # Continue with full image

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": f"public, max-age={settings.MIRA_CACHE_TTL_SECONDS}",
        },
    )

