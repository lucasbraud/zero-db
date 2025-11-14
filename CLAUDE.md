# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack FastAPI template with React frontend, PostgreSQL database, and Docker-based development/deployment. The stack uses FastAPI for the backend API, React with TypeScript for the frontend, SQLModel for ORM, and Traefik as reverse proxy.

## Architecture

### Backend Structure (`backend/app/`)
- `main.py` - FastAPI application entry point with CORS and Sentry configuration
- `models.py` - SQLModel models defining database tables
- `crud.py` - Database CRUD operations
- `api/routes/` - API endpoint modules (login, users, items, utils, private)
- `api/main.py` - Router aggregator combining all route modules
- `core/` - Core functionality:
  - `config.py` - Settings management via Pydantic
  - `db.py` - Database session and engine configuration
  - `security.py` - JWT token handling and password hashing
  - `deps.py` - FastAPI dependency injection functions
- `alembic/` - Database migration files
- `email-templates/` - Email templates (src/ for MJML, build/ for compiled HTML)

### Frontend Structure (`frontend/src/`)
- `routes/` - TanStack Router route definitions and page components
- `components/` - Reusable React components
- `client/` - Auto-generated OpenAPI client (do not edit manually)
- `hooks/` - Custom React hooks
- `theme.tsx` - Chakra UI theme configuration
- `main.tsx` - React application entry point

### Key Architectural Patterns
- Backend uses dependency injection pattern via FastAPI's `Depends()`
- Frontend client is auto-generated from OpenAPI schema
- Database migrations managed via Alembic (must create revision then upgrade)
- JWT authentication with refresh tokens
- Email recovery flows via templates

## Development Commands

### Full Stack Development
```bash
# Start entire stack with live reload
docker compose watch

# Check logs
docker compose logs
docker compose logs backend  # specific service

# Stop services
docker compose stop backend  # or frontend
docker compose down -v  # stop and remove volumes
```

### Backend Development
From `backend/` directory:
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run backend locally (outside Docker)
fastapi dev app/main.py

# Run tests
bash ./scripts/test.sh
# Or if stack is running:
docker compose exec backend bash scripts/tests-start.sh
# Pass pytest args:
docker compose exec backend bash scripts/tests-start.sh -x  # stop on first error

# Database migrations
docker compose exec backend bash
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Access backend container
docker compose exec backend bash
```

### Frontend Development
From `frontend/` directory:
```bash
# Install Node version
fnm install  # or: nvm install
fnm use      # or: nvm use

# Install dependencies
npm install

# Run dev server (outside Docker, recommended for development)
npm run dev

# Lint/format
npm run lint

# Generate API client (after backend OpenAPI changes)
npm run generate-client
# Or use script from root:
./scripts/generate-client.sh

# End-to-end tests with Playwright
docker compose up -d --wait backend
npx playwright test
npx playwright test --ui
```

### Code Quality
```bash
# Run pre-commit hooks manually
uv run pre-commit run --all-files

# Install pre-commit hooks
uv run pre-commit install
```

## Important Development Notes

### Database Changes
Always use Alembic migrations when modifying models:
1. Change model in `backend/app/models.py`
2. Create revision: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply: `alembic upgrade head`

Never modify database schema without migrations in production.

### Frontend Client Generation
Regenerate the frontend client after any backend API changes:
- Client code is in `frontend/src/client/` - never edit manually
- Run `./scripts/generate-client.sh` from root or `npm run generate-client` from frontend/
- Requires backend to be running to fetch OpenAPI schema

### Email Templates
Email templates use MJML. To modify:
1. Edit `.mjml` files in `backend/app/email-templates/src/`
2. Use VS Code MJML extension: `Ctrl+Shift+P` → "MJML: Export to HTML"
3. Save output to `backend/app/email-templates/build/`

### Environment Configuration
- `.env` file contains all environment variables
- Change `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD` before deployment
- Generate secure keys: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- For local testing with subdomains, set `DOMAIN=localhost.tiangolo.com`

### Local Development Ports
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Adminer (DB UI): http://localhost:8080
- Traefik UI: http://localhost:8090

### Docker Compose Overrides
`docker-compose.override.yml` contains development-specific settings:
- Code mounted as volumes for live reload
- `fastapi run --reload` instead of production server
- Local Traefik for subdomain testing

## Testing

### Backend Tests
- Tests in `backend/tests/`
- Uses pytest with coverage
- Coverage report generated in `htmlcov/index.html`
- Tests require database (handled by test fixtures)

### Frontend Tests
- End-to-end tests with Playwright
- Tests require backend running
- Can run in UI mode for debugging

## Scripts

Located in `scripts/`:
- `test.sh` - Run backend tests
- `generate-client.sh` - Generate frontend API client
- `build.sh` - Build Docker images
- `deploy.sh` - Deploy stack

## Common Patterns

### Adding a New API Endpoint
1. Define route in `backend/app/api/routes/<module>.py`
2. Add route to router in `backend/app/api/main.py` if new module
3. Implement CRUD operations in `backend/app/crud.py` if needed
4. Add tests in `backend/tests/api/routes/test_<module>.py`
5. Regenerate frontend client

### Adding a New Model
1. Define SQLModel in `backend/app/models.py`
2. Create Alembic migration
3. Apply migration
4. Add CRUD operations in `backend/app/crud.py`
5. Create API endpoints if needed
6. Regenerate frontend client

### Adding a New Frontend Route
1. Create component in `frontend/src/routes/<path>.tsx`
2. Use TanStack Router conventions for file-based routing
3. Use generated client from `frontend/src/client/` for API calls
4. Use TanStack Query for data fetching and caching

---

## Measurement Control System

This application includes a sophisticated measurement control system for automating measurements on photonic integrated circuits using Suruga Seiki probe stations and EXFO CTP10 vector analyzers.

### Measurement Control Architecture

The measurement control system is built on a **state machine-driven, async-first architecture** that replaces legacy monolithic code with clean, observable, controllable components.

#### Core Design Principles

1. **Async-first:** All operations use `asyncio` for non-blocking execution
2. **State machine:** Immutable state transitions ensure valid state management
3. **Observable:** Real-time progress events broadcast via WebSocket at 1Hz
4. **Controllable:** Pause/resume/cancel at any checkpoint
5. **Testable:** Dependency injection, hardware abstraction, isolated business logic

#### Layer Architecture

**Layer 1: Hardware Abstraction** (`backend/app/hardware/`)
- `base.py` - Base async HTTP client with Result types
- `suruga_seiki.py` - Async wrapper for Suruga Seiki probe station API
  - Movement control (single/2D/3D axes)
  - Optical alignment (flat/focus)
  - Contact detection and retraction
  - Power meter readings
  - I/O control (locks, sensors)
- `exfo_ctp10.py` - Async wrapper for EXFO CTP10 vector analyzer API
  - Measurement configuration
  - Calibration workflows
  - Sweep measurements
  - Live traces and power readings

**Layer 2: State Machine** (`backend/app/core/`)
- `types.py` - Result types (Ok/Err), progress events, enums
- `state_machine.py` - Immutable state machine with validated transitions
  - States: IDLE → CALIBRATING → RUNNING → PAUSED → COMPLETED/FAILED/CANCELLED
  - Events: StartMeasurement, StartDevice, PauseMeasurement, etc.
  - Transition validation ensures impossible states are unrepresentable

**Layer 3: Measurement Controller** (`backend/app/services/`)
- `controller.py` - Async generator orchestrating measurement workflow
  - Yields progress events (DeviceStarted, AlignmentProgress, etc.)
  - Checks pause/cancel events between operations
  - Uses state machine for state management
  - Delegates to hardware clients
- `measurement_manager.py` - Global singleton managing controller lifecycle
  - Spawns background task for measurement run
  - Broadcasts progress to WebSocket clients
  - Coordinates pause/resume/cancel

**Layer 4: Business Services** (Future: Phase 2)
- `calibration.py` - EXFO calibration workflows
- `alignment.py` - Suruga alignment workflows
- `chip_angle.py` - Chip angle calibration
- `executor.py` - Device measurement execution

**Layer 5: Data Layer** (Future: Phase 2)
- `mira_client.py` - Async wrapper for MIRA database API
- `checkpoint.py` - Local checkpoint storage for resume
- `csv_generator.py` - Measurement data CSV generation

**Layer 6: API Layer** (`backend/app/api/routes/`)
- `measurements.py` - REST endpoints for measurement control
  - POST `/measurements/start` - Start measurement
  - POST `/measurements/pause` - Pause measurement
  - POST `/measurements/resume` - Resume measurement
  - POST `/measurements/cancel` - Cancel measurement
  - GET `/measurements/status` - Query status
- `websocket.py` - WebSocket for real-time progress
  - WS `/ws/progress` - Broadcast progress events at 1Hz

### Measurement Control Development

#### Testing Measurement Control (Console)

Use the Python test script to test backend without GUI:

```bash
# From project root
cd backend
uv sync
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install test dependencies
pip install websockets

# Run test script
python ../scripts/test_measurement_control.py
```

The test script:
- Starts a measurement via REST API
- Connects to WebSocket for real-time updates
- Prints formatted progress events to console
- Demonstrates pause/resume/cancel (manual for now)

#### Adding New Hardware Operations

1. Add method to hardware client (`hardware/suruga_seiki.py` or `hardware/exfo_ctp10.py`)
2. Use async/await and return `Result[T, str]` type
3. Add progress event type to `core/types.py`
4. Update controller to yield new event type
5. Update test script to format new event

Example:
```python
# In hardware/suruga_seiki.py
async def new_operation(self, param: int) -> Result[float, str]:
    result = await self._post("/endpoint", json={"param": param})
    if result.is_err():
        return Err(result.error)
    return Ok(result.unwrap()["value"])

# In core/types.py
@dataclass(frozen=True)
class NewOperationCompleted(ProgressEvent):
    value: float
    event_type: str = "new_operation_completed"

# In services/controller.py
async def _process_device(self, device):
    result = await self.suruga.new_operation(42)
    if result.is_ok():
        yield NewOperationCompleted.now(value=result.unwrap())
```

#### State Machine Transitions

All state changes must go through `MeasurementStateMachine.transition()`:

```python
from app.core.state_machine import UpdateOperation

result = self.state_machine.transition(
    self.state,
    UpdateOperation(operation="aligning")
)
if result.is_ok():
    self.state = result.unwrap()
else:
    # Handle invalid transition
    yield ErrorOccurred.now(error=result.error, ...)
```

Valid transitions:
- IDLE → CALIBRATING (StartMeasurement)
- CALIBRATING → RUNNING (CompleteChipAngleCalibration)
- RUNNING → PAUSED (PauseMeasurement)
- PAUSED → RUNNING (ResumeMeasurement)
- RUNNING → COMPLETED (CompleteMeasurement)
- RUNNING/PAUSED → CANCELLED (CancelMeasurement)
- Any → FAILED (FailMeasurement)

#### Progress Event Broadcasting

Progress events are automatically broadcast to all WebSocket clients:

1. Controller yields event
2. MeasurementManager serializes to JSON
3. WebSocketManager broadcasts to all connections
4. Frontend (or test script) receives and displays

Add new event types to `core/types.py` as frozen dataclasses inheriting from `ProgressEvent`.

### External Hardware APIs

The measurement control system integrates with two production-ready FastAPI microservices:

#### 1. Suruga Seiki EW51 API (Port 8001)

**Repository:** `/Users/lucas/Documents/git/github/suruga-seiki-ew51-api`

**Architecture:**
- FastAPI with pythonnet (.NET CLR interop)
- Async task-based pattern (202 Accepted + task_id polling)
- WebSocket streaming at 10 Hz
- Thread-safe with RLock for .NET calls

**Key Endpoints:**

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Connection** | POST `/connection/connect` | Connect to controller (ADS address) |
| | GET `/connection/status` | System status, DLL version, errors |
| **Servo** | POST `/servo/batch/on` | Enable multiple servos (fast) |
| | POST `/servo/batch/off` | Disable multiple servos |
| | POST `/servo/batch/wait_ready` | Wait for InPosition |
| **Motion** | POST `/move/absolute` | Async absolute move → 202 + task_id |
| | POST `/move/relative` | Async relative move → 202 + task_id |
| | GET `/move/status/{task_id}` | Poll task progress |
| | POST `/move/stop/{task_id}` | Cancel movement |
| | POST `/move/2d` | 2D interpolation (sync) |
| | POST `/move/3d` | 3D interpolation (sync) |
| **Position** | GET `/position/all` | All 12 axes positions/status |
| | GET `/position/{axis_number}` | Single axis position |
| **Alignment** | POST `/alignment/flat/execute` | 2D flat alignment → 202 + task_id |
| | POST `/alignment/focus/execute` | 3D focus alignment → 202 + task_id |
| | GET `/alignment/status/{task_id}` | Poll alignment progress |
| | POST `/alignment/stop/{task_id}` | Cancel alignment |
| | GET `/alignment/power` | Power meter reading (dBm) |
| **Profile** | POST `/profile/measure` | Scan measurement (sync or async) |
| | GET `/profile/status/{task_id}` | Poll scan progress |
| **Angle Adj.** | POST `/angle-adjustment/execute` | Contact + angle adjustment → 202 + task_id |
| | GET `/angle-adjustment/status/{task_id}` | Poll adjustment progress |
| **I/O** | POST `/io/digital/output` | Set digital output (locks) |
| | GET `/io/analog/input/{channel}` | Contact sensor voltage |
| **WebSocket** | WS `/ws/position_stream` | Real-time 12-axis + I/O + power (10 Hz) |

**12-Axis Configuration:**
- **Left Stage:** X1(1), Y1(2), Z1(3), TX1(4), TY1(5), TZ1(6)
- **Right Stage:** X2(7), Y2(8), Z2(9), TX2(10), TY2(11), TZ2(12)

**Error Handling:**
- Structured Result types with enums (ErrorCode, StatusCode, PhaseCode)
- HTTP 202 (async task), 400 (invalid), 409 (conflict), 500 (error)
- Detailed error descriptions via `.to_dict()` on enums

**Examples:** See `examples/test_flat_alignment.py`, `test_rest_api_motion.py`, `test_angle_adjustment.py`

#### 2. EXFO CTP10 API (Port 8002)

**Repository:** `/Users/lucas/Documents/git/github/exfo-ctp10-api`

**Architecture:**
- FastAPI with Pymeasure (SCPI communication)
- Async with `asyncio.to_thread()` + lock for SCPI serialization
- WebSocket streaming at configurable rate (default 10 Hz)
- Mock mode for development (`MOCK_MODE=true`)

**Key Endpoints:**

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Connection** | GET `/health` | Health check (connected state) |
| | GET `/connection/status` | Connection status + instrument ID |
| | POST `/connection/connect` | Connect to CTP10 |
| | POST `/connection/disconnect` | Disconnect |
| **Detector** | GET `/detector/snapshot?module=4` | **4-channel snapshot** (ch1-4 power) |
| | GET `/detector/config?module=4&channel=1` | Get detector config |
| | POST `/detector/config?module=4&channel=1` | Set units/resolution |
| | POST `/detector/reference?module=4&channel=1` | Create reference trace |
| | GET `/detector/trace/metadata?module=4&channel=1&trace_type=1` | Get trace info (no download) |
| | GET `/detector/trace/binary?module=4&channel=1&trace_type=1` | **NPY binary trace** (efficient) |
| **TLS** | GET `/tls/{channel}/config` | Get complete TLS config (ch 1-4) |
| | POST `/tls/{channel}/config` | Set wavelength/speed/power/trigger |
| | POST `/tls/{channel}/wavelength?start_nm=X&stop_nm=Y` | Set range |
| | POST `/tls/{channel}/power?power_dbm=X` | Set power (-10 to +10 dBm) |
| | POST `/tls/{channel}/speed?speed_nmps=X` | Set speed (5-200 nm/s) |
| **RLaser** | GET `/rlaser/{laser_number}/config` | Get laser config (lasers 1-10) |
| | POST `/rlaser/{laser_number}/config` | Set wavelength/power/state |
| | POST `/rlaser/{laser_number}/on` | Turn laser ON |
| | POST `/rlaser/{laser_number}/off` | Turn laser OFF |
| **Sweep** | POST `/measurement/sweep/start?wait=false` | Initiate sweep (non-blocking) |
| | GET `/measurement/sweep/status` | Get sweep status/progress |
| | POST `/measurement/sweep/abort` | Abort sweep |
| | GET `/measurement/resolution` | Get resolution (pm) |
| | POST `/measurement/resolution?resolution_pm=X` | Set resolution |
| | GET `/measurement/stabilization` | Get stabilization settings |
| | POST `/measurement/stabilization?output=bool&duration_seconds=X` | Set stabilization |
| **WebSocket** | WS `/ws/power?module=4&interval=0.1` | Real-time 4-channel power (10 Hz) |

**Hardware Capabilities:**
- **Wavelength range:** 1260-1640 nm (C-band + O-band)
- **Sweep speed:** 5-200 nm/s
- **Resolution:** 1-250 pm (standard), 0.02-0.5 pm (high-res)
- **Trace points:** Up to ~940,000 points per trace
- **TLS:** 4 independent channels
- **Reference Lasers:** 10 independent lasers
- **Detector:** 6 channels per module (typical: module 4, ch 1-4)

**Binary Trace Format:**
- NumPy NPY structured array: `data['wavelengths']`, `data['values']`
- Efficiency: ~3.76MB binary vs ~20MB JSON (940k points)
- Usage: `np.load(io.BytesIO(response.content))`

**Error Handling:**
- HTTP 200 (success), 400 (invalid), 500 (error), 503 (not connected)
- JSON errors: `{"detail": "Failed to <operation>: <error>"}`
- SCPI error queue: POST `/connection/check_errors`

**Examples:** See `examples/quick_test.py`, `test_trace_retrieval.py`, `test_snapshot.py`

#### Integration URLs

Configure in `.env`:
```bash
SURUGA_API_URL=http://localhost:8001
EXFO_API_URL=http://localhost:8002
```

For Docker deployment, use service names:
```bash
SURUGA_API_URL=http://suruga-api:8001
EXFO_API_URL=http://exfo-api:8002
```

### Microservice Integration Patterns

#### HTTP Client Wrapper (`backend/app/hardware/`)

Use `httpx.AsyncClient` with Result types for all microservice communication:

```python
# backend/app/hardware/base.py
from typing import TypeVar, Generic
from dataclasses import dataclass
import httpx

T = TypeVar('T')

@dataclass
class Ok(Generic[T]):
    value: T
    def is_ok(self) -> bool: return True
    def is_err(self) -> bool: return False
    def unwrap(self) -> T: return self.value

@dataclass
class Err:
    error: str
    def is_ok(self) -> bool: return False
    def is_err(self) -> bool: return True
    def unwrap(self): raise ValueError(self.error)

Result = Ok[T] | Err

class BaseHardwareClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=timeout)

    async def _get(self, path: str, **kwargs) -> Result[dict]:
        try:
            response = await self.client.get(f"{self.base_url}{path}", **kwargs)
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPStatusError as e:
            return Err(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return Err(str(e))

    async def _post(self, path: str, **kwargs) -> Result[dict]:
        try:
            response = await self.client.post(f"{self.base_url}{path}", **kwargs)
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPStatusError as e:
            return Err(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return Err(str(e))
```

#### Suruga Seiki Client Example

```python
# backend/app/hardware/suruga_seiki.py
from app.hardware.base import BaseHardwareClient, Result, Ok, Err
from typing import List, Dict, Any

class SurugaSeikiClient(BaseHardwareClient):
    """Async wrapper for Suruga Seiki EW51 probe station API."""

    async def connect(self) -> Result[bool]:
        """Connect to probe station controller."""
        result = await self._post("/connection/connect")
        if result.is_err():
            return result
        return Ok(result.unwrap().get("success", True))

    async def get_status(self) -> Result[Dict[str, Any]]:
        """Get system status including DLL version and errors."""
        return await self._get("/connection/status")

    async def enable_servos(self, axes: List[int]) -> Result[bool]:
        """Enable servos for multiple axes (batch operation)."""
        result = await self._post(
            "/servo/batch/on",
            json={"axis_numbers": axes}
        )
        if result.is_err():
            return result
        return Ok(result.unwrap().get("success", True))

    async def get_position(self, axis: int) -> Result[float]:
        """Get current position of single axis."""
        result = await self._get(f"/position/{axis}")
        if result.is_err():
            return result
        data = result.unwrap()
        return Ok(data["current_position"])

    async def get_all_positions(self) -> Result[Dict[int, float]]:
        """Get positions of all 12 axes."""
        result = await self._get("/position/all")
        if result.is_err():
            return result
        data = result.unwrap()
        return Ok({axis: pos["current_position"] for axis, pos in data.items()})

    async def move_absolute(self, axis: int, position: float, speed: float) -> Result[str]:
        """
        Start absolute movement (async task).
        Returns task_id for polling.
        """
        result = await self._post(
            "/move/absolute",
            json={
                "axis_number": axis,
                "target_position": position,
                "speed": speed
            }
        )
        if result.is_err():
            return result
        return Ok(result.unwrap()["task_id"])

    async def get_task_status(self, task_id: str) -> Result[Dict[str, Any]]:
        """Poll async task status."""
        return await self._get(f"/move/status/{task_id}")

    async def cancel_task(self, task_id: str) -> Result[bool]:
        """Cancel running async task."""
        result = await self._post(f"/move/stop/{task_id}")
        if result.is_err():
            return result
        return Ok(True)

    async def start_flat_alignment(
        self,
        left_or_right: str,
        axes: Dict[str, int],
        params: Dict[str, Any]
    ) -> Result[str]:
        """
        Start 2D flat alignment (async task).
        Returns task_id for polling.
        """
        result = await self._post(
            "/alignment/flat/execute",
            json={
                "left_or_right": left_or_right,
                "axis_numbers": axes,
                "params": params
            }
        )
        if result.is_err():
            return result
        return Ok(result.unwrap()["task_id"])

    async def get_power(self) -> Result[float]:
        """Get current power meter reading (dBm)."""
        result = await self._get("/alignment/power")
        if result.is_err():
            return result
        return Ok(result.unwrap()["power_dbm"])
```

#### EXFO CTP10 Client Example

```python
# backend/app/hardware/exfo_ctp10.py
from app.hardware.base import BaseHardwareClient, Result, Ok, Err
import io
import numpy as np

class EXFOCTP10Client(BaseHardwareClient):
    """Async wrapper for EXFO CTP10 vector analyzer API."""

    async def connect(self) -> Result[bool]:
        """Connect to CTP10."""
        result = await self._post("/connection/connect")
        if result.is_err():
            return result
        return Ok(result.unwrap().get("success", True))

    async def get_status(self) -> Result[Dict[str, Any]]:
        """Get connection status and instrument ID."""
        return await self._get("/connection/status")

    async def get_detector_snapshot(self, module: int = 4) -> Result[Dict[str, float]]:
        """
        Get 4-channel detector power snapshot.
        Returns: {ch1_power, ch2_power, ch3_power, ch4_power, wavelength_nm, unit}
        """
        return await self._get(f"/detector/snapshot?module={module}")

    async def configure_tls(
        self,
        channel: int,
        start_nm: float,
        stop_nm: float,
        speed_nmps: int,
        power_dbm: float
    ) -> Result[bool]:
        """Configure TLS channel for sweep."""
        result = await self._post(
            f"/tls/{channel}/config",
            json={
                "start_wavelength_nm": start_nm,
                "stop_wavelength_nm": stop_nm,
                "sweep_speed_nmps": speed_nmps,
                "laser_power_dbm": power_dbm,
                "trigin": 0,  # Software trigger
                "identifier": 1  # C-band
            }
        )
        if result.is_err():
            return result
        return Ok(True)

    async def configure_detector(
        self,
        module: int,
        channel: int,
        resolution_pm: float
    ) -> Result[bool]:
        """Configure detector units and resolution."""
        result = await self._post(
            f"/detector/config?module={module}&channel={channel}",
            json={
                "power_unit": "DBM",
                "spectral_unit": "WAV",
                "resolution_pm": resolution_pm
            }
        )
        if result.is_err():
            return result
        return Ok(True)

    async def start_sweep(self, wait: bool = False) -> Result[bool]:
        """
        Initiate sweep measurement.
        wait=False: Returns immediately (poll status separately)
        wait=True: Blocks until complete
        """
        result = await self._post(f"/measurement/sweep/start?wait={str(wait).lower()}")
        if result.is_err():
            return result
        return Ok(True)

    async def get_sweep_status(self) -> Result[Dict[str, Any]]:
        """
        Get sweep progress.
        Returns: {is_sweeping, is_complete, condition_register}
        """
        return await self._get("/measurement/sweep/status")

    async def abort_sweep(self) -> Result[bool]:
        """Abort current sweep."""
        result = await self._post("/measurement/sweep/abort")
        if result.is_err():
            return result
        return Ok(True)

    async def download_trace_binary(
        self,
        module: int,
        channel: int,
        trace_type: int = 1
    ) -> Result[np.ndarray]:
        """
        Download trace data in efficient binary NPY format.
        trace_type: 1=TF live (calibrated), 11=Raw live, 12=Raw reference

        Returns: Structured array with 'wavelengths' and 'values' fields
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/detector/trace/binary",
                params={"module": module, "channel": channel, "trace_type": trace_type},
                timeout=120.0  # Large traces take time
            )
            response.raise_for_status()

            # Parse NPY binary format
            data = np.load(io.BytesIO(response.content))
            return Ok(data)
        except Exception as e:
            return Err(f"Failed to download trace: {str(e)}")

    async def control_reference_laser(
        self,
        laser_number: int,
        wavelength_nm: float,
        power_dbm: float,
        turn_on: bool
    ) -> Result[bool]:
        """Configure and control reference laser."""
        result = await self._post(
            f"/rlaser/{laser_number}/config",
            json={
                "wavelength_nm": wavelength_nm,
                "power_dbm": power_dbm,
                "power_state": turn_on
            }
        )
        if result.is_err():
            return result
        return Ok(True)
```

#### Async Task Polling Pattern

For long-running operations (Suruga movement, alignment, angle adjustment):

```python
async def wait_for_task_completion(
    client: SurugaSeikiClient,
    task_id: str,
    poll_interval: float = 0.3,
    timeout: float = 300.0,
    cancellation_event: asyncio.Event = None,
    progress_callback: Callable = None
) -> Result[Dict[str, Any]]:
    """
    Poll async task until completion/failure/cancellation.

    Args:
        client: Suruga client instance
        task_id: Task ID from initial POST
        poll_interval: Seconds between status checks
        timeout: Maximum wait time
        cancellation_event: Event to trigger cancellation
        progress_callback: Called with status updates

    Returns:
        Final task status with result data
    """
    start_time = asyncio.get_event_loop().time()

    while True:
        # Check timeout
        if asyncio.get_event_loop().time() - start_time > timeout:
            await client.cancel_task(task_id)
            return Err(f"Task {task_id} timed out after {timeout}s")

        # Check cancellation
        if cancellation_event and cancellation_event.is_set():
            await client.cancel_task(task_id)
            return Err(f"Task {task_id} cancelled by user")

        # Poll status
        result = await client.get_task_status(task_id)
        if result.is_err():
            return result

        status = result.unwrap()

        # Emit progress
        if progress_callback:
            progress_callback(status)

        # Check terminal states
        if status["status"] == "completed":
            return Ok(status)
        elif status["status"] == "failed":
            return Err(f"Task failed: {status.get('error', 'Unknown error')}")
        elif status["status"] == "cancelled":
            return Err("Task was cancelled")

        # Continue polling
        await asyncio.sleep(poll_interval)

# Usage example
async def move_and_wait(suruga: SurugaSeikiClient, axis: int, position: float):
    # Start movement
    result = await suruga.move_absolute(axis, position, speed=100.0)
    if result.is_err():
        return result

    task_id = result.unwrap()

    # Wait for completion with progress tracking
    def log_progress(status):
        print(f"Progress: {status['progress_percent']:.1f}% - Position: {status['current_position']:.3f}")

    return await wait_for_task_completion(
        suruga,
        task_id,
        progress_callback=log_progress
    )
```

#### Sweep Polling Pattern (EXFO)

For EXFO sweeps (synchronous state polling):

```python
async def wait_for_sweep_completion(
    exfo: EXFOCTP10Client,
    poll_interval: float = 0.5,
    timeout: float = 600.0,
    cancellation_event: asyncio.Event = None,
    progress_callback: Callable = None
) -> Result[bool]:
    """
    Poll sweep status until completion.
    EXFO uses state-based polling (not task IDs).
    """
    start_time = asyncio.get_event_loop().time()

    while True:
        if asyncio.get_event_loop().time() - start_time > timeout:
            await exfo.abort_sweep()
            return Err(f"Sweep timed out after {timeout}s")

        if cancellation_event and cancellation_event.is_set():
            await exfo.abort_sweep()
            return Err("Sweep cancelled by user")

        result = await exfo.get_sweep_status()
        if result.is_err():
            return result

        status = result.unwrap()

        if progress_callback:
            progress_callback(status)

        if status["is_complete"]:
            return Ok(True)

        if not status["is_sweeping"]:
            return Err("Sweep stopped unexpectedly")

        await asyncio.sleep(poll_interval)

# Usage example
async def execute_sweep(exfo: EXFOCTP10Client):
    # Configure TLS
    await exfo.configure_tls(
        channel=1,
        start_nm=1530.0,
        stop_nm=1565.0,
        speed_nmps=100,
        power_dbm=0.0
    )

    # Configure detector
    await exfo.configure_detector(module=4, channel=1, resolution_pm=10.0)

    # Start sweep (non-blocking)
    result = await exfo.start_sweep(wait=False)
    if result.is_err():
        return result

    # Wait for completion
    result = await wait_for_sweep_completion(
        exfo,
        progress_callback=lambda s: print(f"Sweeping: {s['is_sweeping']}")
    )
    if result.is_err():
        return result

    # Download trace
    return await exfo.download_trace_binary(module=4, channel=1, trace_type=1)
```

#### Integration Workflow Examples

**Example 1: Chip Angle Calibration**

```python
async def calibrate_chip_angle(
    suruga: SurugaSeikiClient,
    exfo: EXFOCTP10Client,
    stage: str = "LEFT"  # or "RIGHT"
) -> Result[float]:
    """
    Calibrate chip angle using contact detection and angle adjustment.
    """
    # 1. Enable servos
    axes = list(range(1, 13))  # All 12 axes
    result = await suruga.enable_servos(axes)
    if result.is_err():
        return result

    # 2. Retract Z-axis before contact
    z_axis = 3 if stage == "LEFT" else 9
    result = await suruga.move_absolute(z_axis, position=-100.0, speed=50.0)
    if result.is_err():
        return result
    task_id = result.unwrap()
    result = await wait_for_task_completion(suruga, task_id)
    if result.is_err():
        return result

    # 3. Unlock contact sensor
    channel = 1 if stage == "LEFT" else 2
    await suruga._post("/io/digital/output", json={"channel": channel, "state": False})

    # 4. Start angle adjustment (contact detection + TX/TY adjustment)
    result = await suruga._post(
        "/angle-adjustment/execute",
        json={
            "left_or_right": stage,
            "adjust_tx": True,
            "adjust_ty": True,
            "axis_numbers": {
                "z": z_axis,
                "tx": 4 if stage == "LEFT" else 10,
                "ty": 5 if stage == "LEFT" else 11
            }
        }
    )
    if result.is_err():
        return result

    task_id = result.unwrap()["task_id"]

    # 5. Wait for completion with progress tracking
    def log_progress(status):
        phase = status.get("phase", "unknown")
        progress = status.get("progress_percent", 0)
        print(f"Angle adjustment: {phase} - {progress:.1f}%")

    result = await wait_for_task_completion(
        suruga,
        task_id,
        timeout=300.0,
        progress_callback=log_progress
    )
    if result.is_err():
        return result

    # 6. Extract final angle
    final_status = result.unwrap()
    angle = final_status.get("final_angle", 0.0)

    return Ok(angle)
```

**Example 2: Device Measurement**

```python
async def measure_device(
    suruga: SurugaSeikiClient,
    exfo: EXFOCTP10Client,
    device_position: Dict[str, float],
    wavelength_range: tuple[float, float]
) -> Result[np.ndarray]:
    """
    Complete device measurement workflow:
    1. Move to device position
    2. Perform optical alignment
    3. Execute sweep measurement
    4. Download trace data
    """
    # 1. Move to device
    for axis, position in device_position.items():
        result = await suruga.move_absolute(axis, position, speed=100.0)
        if result.is_err():
            return result
        task_id = result.unwrap()
        result = await wait_for_task_completion(suruga, task_id)
        if result.is_err():
            return result

    # 2. Optical alignment (flat + focus)
    result = await suruga.start_flat_alignment(
        left_or_right="LEFT",
        axes={"x": 1, "y": 2, "z": 3},
        params={
            "field_search_range": 50.0,
            "peak_search_range": 20.0,
            "convergence_threshold": 0.1
        }
    )
    if result.is_err():
        return result

    task_id = result.unwrap()
    result = await wait_for_task_completion(suruga, task_id, timeout=120.0)
    if result.is_err():
        return result

    # 3. Configure EXFO for sweep
    await exfo.configure_tls(
        channel=1,
        start_nm=wavelength_range[0],
        stop_nm=wavelength_range[1],
        speed_nmps=100,
        power_dbm=0.0
    )
    await exfo.configure_detector(module=4, channel=1, resolution_pm=10.0)

    # 4. Execute sweep
    result = await exfo.start_sweep(wait=False)
    if result.is_err():
        return result

    result = await wait_for_sweep_completion(exfo, timeout=300.0)
    if result.is_err():
        return result

    # 5. Download trace
    return await exfo.download_trace_binary(module=4, channel=1, trace_type=1)
```

#### WebSocket Integration for Real-Time Monitoring

```python
# backend/app/services/hardware_monitor.py
import asyncio
import websockets
from typing import Callable, Optional

class HardwareMonitor:
    """Monitor hardware status via WebSocket streams."""

    def __init__(self, suruga_url: str, exfo_url: str):
        self.suruga_ws_url = suruga_url.replace("http", "ws") + "/ws/position_stream"
        self.exfo_ws_url = exfo_url.replace("http", "ws") + "/ws/power?module=4&interval=0.1"
        self.running = False

    async def stream_positions(self, callback: Callable):
        """Stream real-time position data from Suruga."""
        async with websockets.connect(self.suruga_ws_url) as ws:
            while self.running:
                message = await ws.recv()
                data = json.loads(message)
                callback(data)  # {axes: {1: pos, 2: pos, ...}, io: {...}, power: [...]}

    async def stream_power(self, callback: Callable):
        """Stream real-time power data from EXFO."""
        async with websockets.connect(self.exfo_ws_url) as ws:
            while self.running:
                message = await ws.recv()
                data = json.loads(message)
                callback(data)  # {ch1_power, ch2_power, ch3_power, ch4_power, ...}

    async def start(self, position_callback: Callable, power_callback: Callable):
        """Start both WebSocket streams."""
        self.running = True
        await asyncio.gather(
            self.stream_positions(position_callback),
            self.stream_power(power_callback)
        )

    def stop(self):
        """Stop streaming."""
        self.running = False
```

#### Error Handling Best Practices

1. **Always check Result types:**
```python
result = await suruga.move_absolute(1, 100.0, 50.0)
if result.is_err():
    # Log error, emit progress event, or raise exception
    logger.error(f"Movement failed: {result.error}")
    yield ErrorOccurred.now(error=result.error, operation="move_absolute")
    return

task_id = result.unwrap()  # Safe after is_err() check
```

2. **Structured error responses from microservices:**
```python
# Suruga returns structured errors with enums
{
  "success": false,
  "error_code": "SERVO_IS_NOT_READY",
  "error_value": 2,
  "error_description": "Servo is not ready",
  "error_message": "Cannot move: servo not enabled"
}

# EXFO returns simple detail messages
{
  "detail": "Failed to start sweep: CTP10 not connected"
}
```

3. **Graceful degradation:**
```python
# Try operation with retries
for attempt in range(3):
    result = await exfo.get_detector_snapshot()
    if result.is_ok():
        break
    await asyncio.sleep(1.0)
else:
    return Err("Failed to get detector snapshot after 3 attempts")
```

#### Testing Strategies

1. **Unit tests with mocked HTTP clients:**
```python
# tests/hardware/test_suruga_client.py
import pytest
from unittest.mock import AsyncMock, patch
from app.hardware.suruga_seiki import SurugaSeikiClient

@pytest.mark.asyncio
async def test_move_absolute_success():
    client = SurugaSeikiClient("http://localhost:8001")

    with patch.object(client, '_post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Ok({"task_id": "test-123"})

        result = await client.move_absolute(1, 100.0, 50.0)

        assert result.is_ok()
        assert result.unwrap() == "test-123"
        mock_post.assert_called_once()
```

2. **Integration tests with real microservices:**
```python
# tests/integration/test_measurement_workflow.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_measurement_workflow():
    suruga = SurugaSeikiClient(os.getenv("SURUGA_API_URL"))
    exfo = EXFOCTP10Client(os.getenv("EXFO_API_URL"))

    # Test connection
    result = await suruga.connect()
    assert result.is_ok()

    result = await exfo.connect()
    assert result.is_ok()

    # Test measurement workflow
    result = await measure_device(
        suruga,
        exfo,
        device_position={"1": 1000.0, "2": 2000.0},
        wavelength_range=(1530.0, 1565.0)
    )

    assert result.is_ok()
    trace_data = result.unwrap()
    assert len(trace_data) > 0
```

3. **Use mock mode for EXFO during development:**
```env
# .env for development
EXFO_API_URL=http://localhost:8002
EXFO_MOCK_MODE=true  # Pass to EXFO API
```

### Implementation Status

**Phase 1 (Current): Backend Core** ✅
- Hardware abstraction layer
- State machine
- Measurement controller (basic structure)
- FastAPI endpoints
- WebSocket broadcasting
- Python test script

**Phase 2 (Next): Backend Services** 🚧
- HTTP client wrappers (suruga_seiki.py, exfo_ctp10.py)
- Async task polling utilities
- MIRA database integration
- Calibration workflows (chip angle, EXFO calibration)
- Alignment orchestration (flat/focus with retry logic)
- Movement logic with angle correction
- Contact detection with retraction
- Power checking and alignment decision
- EXFO sweep execution with progress tracking
- Binary trace download and processing
- CSV generation and upload
- Checkpoint/resume support

**Phase 3 (Future): Frontend Foundation** 📋
- Measurement dashboard page
- Control panel (start/pause/cancel)
- WebSocket integration
- Progress visualization
- Error display

**Phase 4 (Future): Frontend Polish** 📋
- Real-time power charts (EXFO WebSocket)
- Stage position visualization (Suruga WebSocket)
- Log viewer
- Measurement history

### Key Differences from Legacy Code

| Legacy Code | New Architecture |
|-------------|------------------|
| 992-line monolithic method | Async generator with ~50-line methods |
| `print()` statements | Progress events via WebSocket |
| No pause/cancel | Pause/resume/cancel at checkpoints |
| Imperative state mutations | Immutable state machine transitions |
| Blocking operations | Async/await non-blocking |
| Try/except swallows errors | Result types with explicit error handling |
| Hard to debug | Observable state, structured logging |
| No tests possible | Dependency injection, mockable |

### Debugging Measurement Control

1. **Check WebSocket events:** Connect to `ws://localhost:8000/api/v1/ws/progress` and watch real-time events
2. **Query state:** GET `/api/v1/measurements/status` for current state snapshot
3. **Check hardware APIs:** Verify Suruga and EXFO servers are running and responding
4. **Backend logs:** `docker compose logs backend` shows FastAPI logs
5. **Test script:** Use `scripts/test_measurement_control.py` to isolate backend issues

### Development Workflow with Microservices

#### Running Microservices Locally

**Terminal 1: Suruga Seiki API**
```bash
cd /Users/lucas/Documents/git/github/suruga-seiki-ew51-api
uv sync
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
fastapi dev app/main.py --port 8001
```

Access at: http://localhost:8001/docs

**Terminal 2: EXFO CTP10 API**
```bash
cd /Users/lucas/Documents/git/github/exfo-ctp10-api
uv sync
source .venv/bin/activate
fastapi dev app/main.py --port 8002
```

Access at: http://localhost:8002/docs

**EXFO Mock Mode (Development without Hardware):**
```bash
# In exfo-ctp10-api/.env
MOCK_MODE=true
AUTO_CONNECT=true
```

**Terminal 3: Zero-DB Backend**
```bash
cd /Users/lucas/Documents/git/github/zero-db/backend
uv sync
source .venv/bin/activate

# Set microservice URLs in .env
echo "SURUGA_API_URL=http://localhost:8001" >> .env
echo "EXFO_API_URL=http://localhost:8002" >> .env

fastapi dev app/main.py
```

Access at: http://localhost:8000/docs

#### Docker Compose Integration

Add microservices to `docker-compose.yml`:

```yaml
services:
  # Existing services (backend, frontend, db, etc.)
  # ...

  suruga-api:
    build:
      context: ../suruga-seiki-ew51-api
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - LOG_LEVEL=INFO
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  exfo-api:
    build:
      context: ../exfo-ctp10-api
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      - MOCK_MODE=${EXFO_MOCK_MODE:-false}
      - AUTO_CONNECT=true
      - LOG_LEVEL=INFO
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  app-network:
    driver: bridge
```

Update backend service URLs:
```yaml
  backend:
    # ... existing config
    environment:
      - SURUGA_API_URL=http://suruga-api:8001
      - EXFO_API_URL=http://exfo-api:8002
      # ... other env vars
    depends_on:
      suruga-api:
        condition: service_healthy
      exfo-api:
        condition: service_healthy
```

Start entire stack:
```bash
docker compose up -d
docker compose logs -f  # Follow logs
```

#### Testing Microservice Integration

**Quick Health Check:**
```bash
# Test all microservices are up
curl http://localhost:8001/connection/status  # Suruga
curl http://localhost:8002/health  # EXFO
curl http://localhost:8000/api/v1/health  # Zero-DB
```

**Test Suruga API Endpoints:**
```bash
# From suruga-seiki-ew51-api/examples/
cd /Users/lucas/Documents/git/github/suruga-seiki-ew51-api/examples

# Test REST API motion with task polling
python test_rest_api_motion.py

# Test flat alignment with visualization
python test_flat_alignment.py

# Test angle adjustment
python test_angle_adjustment.py
```

**Test EXFO API Endpoints:**
```bash
# From exfo-ctp10-api/examples/
cd /Users/lucas/Documents/git/github/exfo-ctp10-api/examples

# Quick sanity check (all endpoints)
python quick_test.py

# Test 4-channel detector snapshot
python test_snapshot.py

# Test full sweep with trace download
python test_trace_retrieval.py

# Test WebSocket streaming
python debug_websocket.py
```

**Test Integration from Zero-DB:**
```bash
# From zero-db/backend/
cd /Users/lucas/Documents/git/github/zero-db/backend

# Create test script: scripts/test_microservice_integration.py
cat > scripts/test_microservice_integration.py << 'EOF'
import asyncio
import os
from app.hardware.suruga_seiki import SurugaSeikiClient
from app.hardware.exfo_ctp10 import EXFOCTP10Client

async def main():
    suruga_url = os.getenv("SURUGA_API_URL", "http://localhost:8001")
    exfo_url = os.getenv("EXFO_API_URL", "http://localhost:8002")

    suruga = SurugaSeikiClient(suruga_url)
    exfo = EXFOCTP10Client(exfo_url)

    # Test Suruga connection
    print("Testing Suruga connection...")
    result = await suruga.get_status()
    if result.is_ok():
        print(f"✓ Suruga connected: {result.unwrap()}")
    else:
        print(f"✗ Suruga error: {result.error}")

    # Test EXFO connection
    print("\nTesting EXFO connection...")
    result = await exfo.get_status()
    if result.is_ok():
        print(f"✓ EXFO connected: {result.unwrap()}")
    else:
        print(f"✗ EXFO error: {result.error}")

    # Test detector snapshot
    print("\nTesting EXFO detector snapshot...")
    result = await exfo.get_detector_snapshot(module=4)
    if result.is_ok():
        snapshot = result.unwrap()
        print(f"✓ Power readings:")
        print(f"  CH1: {snapshot['ch1_power']:.2f} dBm")
        print(f"  CH2: {snapshot['ch2_power']:.2f} dBm")
        print(f"  CH3: {snapshot['ch3_power']:.2f} dBm")
        print(f"  CH4: {snapshot['ch4_power']:.2f} dBm")
    else:
        print(f"✗ Snapshot error: {result.error}")

    # Test Suruga position query
    print("\nTesting Suruga position query...")
    result = await suruga.get_all_positions()
    if result.is_ok():
        positions = result.unwrap()
        print(f"✓ Axis positions (first 4):")
        for axis in range(1, 5):
            print(f"  Axis {axis}: {positions[axis]:.3f} µm")
    else:
        print(f"✗ Position error: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run integration test
python scripts/test_microservice_integration.py
```

#### Development Tips

**1. Use OpenAPI Interactive Docs:**
- Suruga: http://localhost:8001/docs
- EXFO: http://localhost:8002/docs
- Zero-DB: http://localhost:8000/docs

All endpoints are documented with schemas, examples, and Try It Out functionality.

**2. Monitor Real-Time Data with WebSocket Tools:**

Using `websocat` (install: `brew install websocat` / `apt install websocat`):
```bash
# Monitor Suruga positions
websocat ws://localhost:8001/ws/position_stream

# Monitor EXFO power
websocat "ws://localhost:8002/ws/power?module=4&interval=0.1"

# Monitor Zero-DB measurement progress
websocat ws://localhost:8000/api/v1/ws/progress
```

Using Python:
```python
import asyncio
import websockets
import json

async def monitor_power():
    uri = "ws://localhost:8002/ws/power?module=4&interval=0.1"
    async with websockets.connect(uri) as ws:
        for i in range(10):
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"CH1: {data['ch1_power']:.2f} dBm | CH2: {data['ch2_power']:.2f} dBm")

asyncio.run(monitor_power())
```

**3. Debugging Async Task Polling:**

Add verbose logging to see task state transitions:
```python
# In hardware client
import logging
logger = logging.getLogger(__name__)

async def wait_for_task_completion(client, task_id, ...):
    while True:
        result = await client.get_task_status(task_id)
        if result.is_ok():
            status = result.unwrap()
            logger.info(f"Task {task_id}: {status['status']} - {status.get('progress_percent', 0):.1f}%")
            # ... rest of logic
```

**4. Use EXFO Mock Mode for Rapid Development:**

Mock mode simulates realistic responses without hardware:
- Detector snapshot returns random power values (-20 to -5 dBm)
- Sweep completes after configurable delay
- Trace download returns Gaussian-shaped data
- All endpoints return success responses

**5. Profile Microservice Performance:**

```bash
# Time endpoint response
time curl -X GET http://localhost:8002/detector/snapshot?module=4

# Measure trace download time
time curl -X GET "http://localhost:8002/detector/trace/binary?module=4&channel=1&trace_type=1" -o trace.npy

# Profile task polling overhead
python -m cProfile -o profile.stats scripts/test_microservice_integration.py
```

**6. Parallel Development Workflow:**

You can work on microservices and zero-db simultaneously:
- Make changes to microservice code
- Microservices auto-reload (fastapi dev mode)
- Zero-DB picks up changes immediately (no restart needed)
- Test integration in real-time

**7. Error Simulation for Testing:**

In Suruga API, simulate errors:
```python
# In suruga-seiki-ew51-api, temporarily modify controller_manager.py
def move_absolute(...):
    # Simulate servo not ready error
    if simulate_error:
        return {
            "success": False,
            "error_code": "SERVO_IS_NOT_READY",
            "error_value": 2
        }
```

In EXFO API, use mock mode with injected failures:
```python
# In exfo-ctp10-api/app/mocks/mock_ctp10.py
class FakeCTP10:
    def __init__(self, fail_sweep=False):
        self.fail_sweep = fail_sweep
```

**8. Deployment Checklist:**

Before deploying to production:
- [ ] Set `EXFO_MOCK_MODE=false`
- [ ] Configure real hardware IPs in microservice `.env` files
- [ ] Test hardware connectivity: `curl http://<suruga-ip>:8001/connection/status`
- [ ] Verify all 3 services can reach each other (network configuration)
- [ ] Test full measurement workflow end-to-end
- [ ] Monitor logs for warnings/errors: `docker compose logs -f`
- [ ] Set up health check monitoring (Prometheus/Grafana recommended)
- [ ] Configure backup strategy for measurement data
- [ ] Document hardware-specific calibration parameters

#### Common Issues and Solutions

**Issue: "Connection refused" when accessing microservices**
- Solution: Verify microservices are running: `ps aux | grep fastapi`
- Check ports: `lsof -i :8001` and `lsof -i :8002`
- In Docker: Check service health: `docker compose ps`

**Issue: Task polling timeout**
- Solution: Increase timeout in `wait_for_task_completion(timeout=600.0)`
- Check hardware is responding: Test endpoint directly in browser
- Verify task_id is correct (not expired/invalid)

**Issue: WebSocket disconnect**
- Solution: Implement reconnection logic with exponential backoff
- Check for firewall blocking WebSocket connections
- Verify WebSocket URL uses `ws://` not `http://`

**Issue: Binary trace download fails**
- Solution: Increase httpx timeout: `AsyncClient(timeout=120.0)`
- Check available memory (traces can be ~4MB)
- Verify trace_type is valid (1=TF live, 11=Raw live)

**Issue: EXFO sweep never completes**
- Solution: Check `is_sweeping` and `condition_register` in status
- Verify TLS configuration is valid (wavelength range, speed)
- Call `/connection/check_errors` to query SCPI error queue

**Issue: Suruga movement doesn't start**
- Solution: Check servo is enabled: POST `/servo/batch/on`
- Verify axis is within limits: GET `/position/{axis}`
- Check task status for error details: GET `/move/status/{task_id}`
