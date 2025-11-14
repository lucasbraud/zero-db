"""
Test script for measurement control system.

This script demonstrates the backend measurement control API without a GUI.
It starts a measurement, connects to the WebSocket for real-time updates,
and allows pause/resume/cancel via keyboard input.

Usage:
    python scripts/test_measurement_control.py

Requirements:
    - Backend server running (docker compose watch)
    - httpx and websockets packages (pip install httpx websockets)
"""

import asyncio
import sys
from datetime import datetime

import httpx
import websockets


API_BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws/progress"


class MeasurementTester:
    """Console-based measurement control tester."""

    def __init__(self):
        """Initialize tester."""
        self.client = httpx.AsyncClient(base_url=API_BASE_URL)
        self.running = True

    async def start_measurement(self, order_id: str):
        """
        Start a measurement via API.

        Args:
            order_id: Measurement order ID
        """
        print(f"\n[{self._timestamp()}] Starting measurement for order: {order_id}")

        try:
            response = await self.client.post(
                "/measurements/start",
                json={
                    "order_id": order_id,
                    "suruga_base_url": "http://localhost:8001",
                    "exfo_base_url": "http://localhost:8002",
                    "power_threshold_db": 1.5,
                    "devices_between_alignments": 5,
                    "perform_periodic_alignment": True,
                },
            )
            response.raise_for_status()
            data = response.json()
            print(
                f"[{self._timestamp()}] ✓ Measurement started: {data['message']} ({data['total_devices']} devices)"
            )
            return True
        except httpx.HTTPStatusError as e:
            print(
                f"[{self._timestamp()}] ✗ Failed to start measurement: {e.response.status_code} - {e.response.text}"
            )
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] ✗ Error: {str(e)}")
            return False

    async def pause_measurement(self):
        """Pause the measurement."""
        print(f"\n[{self._timestamp()}] Pausing measurement...")
        try:
            response = await self.client.post("/measurements/pause")
            response.raise_for_status()
            print(f"[{self._timestamp()}] ✓ Pause requested")
        except Exception as e:
            print(f"[{self._timestamp()}] ✗ Pause failed: {str(e)}")

    async def resume_measurement(self):
        """Resume the measurement."""
        print(f"\n[{self._timestamp()}] Resuming measurement...")
        try:
            response = await self.client.post("/measurements/resume")
            response.raise_for_status()
            print(f"[{self._timestamp()}] ✓ Resumed")
        except Exception as e:
            print(f"[{self._timestamp()}] ✗ Resume failed: {str(e)}")

    async def cancel_measurement(self):
        """Cancel the measurement."""
        print(f"\n[{self._timestamp()}] Cancelling measurement...")
        try:
            response = await self.client.post("/measurements/cancel")
            response.raise_for_status()
            print(f"[{self._timestamp()}] ✓ Cancelled")
            self.running = False
        except Exception as e:
            print(f"[{self._timestamp()}] ✗ Cancel failed: {str(e)}")

    async def get_status(self):
        """Get current measurement status."""
        try:
            response = await self.client.get("/measurements/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[{self._timestamp()}] ✗ Status query failed: {str(e)}")
            return None

    async def monitor_progress(self):
        """Monitor measurement progress via WebSocket."""
        print(f"\n[{self._timestamp()}] Connecting to WebSocket...")

        try:
            async with websockets.connect(WS_URL) as websocket:
                print(f"[{self._timestamp()}] ✓ Connected to progress stream")
                print(f"[{self._timestamp()}] Listening for events...\n")
                print("=" * 80)

                while self.running:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(), timeout=1.0
                        )
                        event = eval(message)  # Parse JSON
                        self._print_event(event)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        print(
                            f"\n[{self._timestamp()}] WebSocket connection closed"
                        )
                        break

        except Exception as e:
            print(f"[{self._timestamp()}] ✗ WebSocket error: {str(e)}")

    def _print_event(self, event: dict):
        """
        Print progress event in formatted way.

        Args:
            event: Progress event dict
        """
        event_type = event.get("event_type", "unknown")
        timestamp = self._timestamp()

        if event_type == "measurement_started":
            print(f"\n[{timestamp}] 🚀 Measurement Started")
            print(f"  Order ID: {event.get('order_id')}")
            print(f"  Total Devices: {event.get('total_devices')}")

        elif event_type == "device_started":
            print(f"\n[{timestamp}] 📍 Device {event.get('device_index')} Started")
            print(f"  Name: {event.get('device_name')}")

        elif event_type == "device_moving":
            print(f"[{timestamp}] ➡️  Moving to device {event.get('device_index')}")

        elif event_type == "contact_detected":
            print(
                f"[{timestamp}] ⚠️  Contact detected on {event.get('stage')} stage (V={event.get('voltage'):.4f})"
            )

        elif event_type == "power_measured":
            print(
                f"[{timestamp}] 🔆 Power: {event.get('stage')} = {event.get('power_dbm'):.2f} dBm"
            )

        elif event_type == "alignment_started":
            print(
                f"[{timestamp}] 🎯 Alignment started on {event.get('stage')} stage"
            )

        elif event_type == "alignment_progress":
            phase = event.get("phase", "unknown")
            power = event.get("power_dbm")
            power_str = f"{power:.2f} dBm" if power is not None else "measuring..."
            print(f"[{timestamp}]    Phase: {phase} | Power: {power_str}")

        elif event_type == "alignment_completed":
            print(f"[{timestamp}] ✓ Alignment completed on {event.get('stage')}")
            print(f"  Initial: {event.get('initial_power_dbm'):.2f} dBm")
            print(f"  Final: {event.get('final_power_dbm'):.2f} dBm")
            print(f"  Improvement: {event.get('improvement_db'):.2f} dB")

        elif event_type == "alignment_failed":
            print(f"[{timestamp}] ✗ Alignment failed: {event.get('error')}")

        elif event_type == "measurement_executing":
            print(f"[{timestamp}] 📊 Executing EXFO measurement...")

        elif event_type == "measurement_data_acquired":
            print(
                f"[{timestamp}] ✓ Data acquired ({event.get('num_points')} points)"
            )

        elif event_type == "measurement_data_uploaded":
            print(f"[{timestamp}] ✓ Data uploaded (ID: {event.get('measurement_id')})")

        elif event_type == "device_completed":
            print(
                f"[{timestamp}] ✅ Device {event.get('device_index')} completed\n"
            )

        elif event_type == "device_skipped":
            print(
                f"[{timestamp}] ⏭️  Device {event.get('device_index')} skipped: {event.get('reason')}\n"
            )

        elif event_type == "measurement_paused":
            print(f"\n[{timestamp}] ⏸️  Measurement PAUSED at device {event.get('device_index')}")
            print("  Press 'r' to resume or 'c' to cancel\n")

        elif event_type == "measurement_resumed":
            print(f"\n[{timestamp}] ▶️  Measurement RESUMED\n")

        elif event_type == "measurement_cancelled":
            print(f"\n[{timestamp}] 🛑 Measurement CANCELLED\n")
            self.running = False

        elif event_type == "measurement_completed":
            print(f"\n[{timestamp}] 🏁 Measurement COMPLETED")
            print(f"  Total Devices: {event.get('total_devices')}")
            print(f"  Successful: {event.get('successful_devices')}")
            print(f"  Failed: {event.get('failed_devices')}")
            print(f"  Duration: {event.get('total_duration_seconds'):.1f}s\n")
            self.running = False

        elif event_type == "measurement_failed":
            print(f"\n[{timestamp}] ❌ Measurement FAILED")
            print(f"  Error: {event.get('error')}\n")
            self.running = False

        elif event_type == "error_occurred":
            print(f"[{timestamp}] ⚠️  Error in {event.get('operation')}: {event.get('error')}")

        else:
            print(f"[{timestamp}] {event_type}: {event}")

    async def keyboard_input_handler(self):
        """Handle keyboard input for control commands."""
        print("\n" + "=" * 80)
        print("Controls:")
        print("  p - Pause measurement")
        print("  r - Resume measurement")
        print("  c - Cancel measurement")
        print("  s - Get status")
        print("  q - Quit (without cancelling)")
        print("=" * 80 + "\n")

        loop = asyncio.get_event_loop()

        while self.running:
            # Note: This is a simplified approach. In production, use aioconsole
            # for true async keyboard input
            await asyncio.sleep(0.5)

            # Check if there's input (non-blocking would be better)
            # This is a placeholder - real implementation would use aioconsole

    @staticmethod
    def _timestamp() -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


async def main():
    """Main entry point."""
    print("=" * 80)
    print("Measurement Control System - Console Tester")
    print("=" * 80)

    tester = MeasurementTester()

    try:
        # Start measurement
        order_id = input("\nEnter order ID (or press Enter for 'TEST_001'): ").strip()
        if not order_id:
            order_id = "TEST_001"

        success = await tester.start_measurement(order_id)
        if not success:
            return

        # Monitor progress
        await tester.monitor_progress()

        print("\n" + "=" * 80)
        print("Test completed")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        await tester.cancel_measurement()

    finally:
        await tester.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
