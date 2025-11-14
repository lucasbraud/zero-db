# Architecture Decision: External Hardware APIs

## Decision

**Hardware control APIs (Suruga Seiki, EXFO CTP10) are maintained as separate repositories and communicate with the measurement control system via HTTP.**

## Context

The measurement control system needs to interact with:
1. Suruga Seiki EW51 probe station (2x6 axis stages)
2. EXFO CTP10 vector analyzer (sweep laser and detector)

These could be:
- **Option A:** Separate FastAPI services in their own repos (chosen)
- **Option B:** Embedded as modules within the measurement control app
- **Option C:** Direct hardware libraries imported into measurement control

## Rationale

### Single Responsibility Principle
Each service has one job:
- **Suruga Seiki API:** Control probe station hardware (pythonnet → .NET DLL)
- **EXFO CTP10 API:** Control vector analyzer (Pymeasure → VISA)
- **Measurement Control:** Orchestrate measurements, manage workflow, provide GUI

### Reusability
Hardware APIs can be used by multiple consumers:
- This measurement control application
- Manual testing scripts
- Calibration routines
- Other research experiments
- Future applications

If embedded, they're locked to this app. As separate services, they're universal building blocks.

### Development Velocity
- Hardware team works on APIs independently
- Measurement team works on orchestration independently
- No merge conflicts between teams
- Each repo has its own dependencies, tests, release cycle

### Fault Isolation
Service crashes are isolated:
- EXFO API crash → doesn't affect Suruga API or measurement backend
- Measurement backend crash → doesn't affect hardware APIs
- Restart only the failed service
- Measurement controller detects reconnection and retries

### Version Management
```
Measurement Control v2.0
├─ Suruga API v1.3.2 (stable, tested)
├─ EXFO API v2.0.0-beta (new Pymeasure driver)
└─ Independent upgrade paths
```

Pin hardware API versions while upgrading measurement logic, or vice versa.

### Deployment Flexibility
**Development:**
- All services on localhost (8000/8001/8002)

**Production:**
- Suruga API on machine connected to probe station
- EXFO API on machine connected to vector analyzer
- Measurement control on any machine that can reach them
- Frontend hosted separately

Physical hardware location doesn't dictate software architecture.

## Communication Pattern

```
┌─────────────────┐
│ Frontend (React)│
│  Port: 5173     │
└────────┬────────┘
         │ HTTP + WebSocket
         ↓
┌─────────────────────────┐
│ Measurement Control API │
│  Port: 8000             │
└───────┬────────┬────────┘
        │        │
   HTTP │        │ HTTP
        ↓        ↓
┌──────────┐  ┌──────────┐
│ Suruga   │  │ EXFO     │
│ Seiki API│  │ CTP10 API│
│ Port:8001│  │ Port:8002│
└────┬─────┘  └────┬─────┘
     │             │
pythonnet      Pymeasure
     │             │
  .NET DLL      VISA
     │             │
     ↓             ↓
[Probe Station] [Vector Analyzer]
```

## Repository Structure

```
C:\Users\pic_s\git\
├── probe-flow/
│   └── instruments/
│       └── suruga_seiki_ew51/          # Existing repo
│           ├── controller_manager.py   # .NET interop
│           ├── routers/                # FastAPI endpoints
│           │   ├── motion.py
│           │   ├── alignment.py
│           │   ├── position.py
│           │   └── io.py
│           ├── models.py               # Pydantic models
│           └── main.py                 # FastAPI app
│
├── exfo-ctp10-api/                     # New repo (to be created)
│   ├── instrument/
│   │   └── exfo_driver.py              # Pymeasure wrapper
│   ├── routers/
│   │   ├── configure.py                # Set parameters
│   │   ├── calibrate.py                # Reference creation
│   │   ├── measure.py                  # Execute sweep
│   │   └── power.py                    # Power readings
│   ├── models.py                       # Pydantic models
│   ├── main.py                         # FastAPI app
│   └── README.md
│
└── zero-db/                            # Measurement control (this repo)
    ├── backend/
    │   └── app/
    │       ├── hardware/               # Async HTTP clients
    │       │   ├── base.py             # Base client with Result types
    │       │   ├── suruga_seiki.py     # Wraps probe-flow API
    │       │   └── exfo_ctp10.py       # Wraps exfo-ctp10-api
    │       ├── services/               # Orchestration logic
    │       │   ├── controller.py       # Main workflow
    │       │   ├── calibration.py      # EXFO calibration
    │       │   ├── alignment.py        # Alignment orchestration
    │       │   └── executor.py         # Device execution
    │       ├── core/                   # State machine, types
    │       └── api/routes/             # REST + WebSocket endpoints
    ├── frontend/                       # GUI dashboard
    └── docs/
        └── ARCHITECTURE.md             # This document
```

## Hardware Abstraction Layer

The measurement control system uses async HTTP clients to communicate with hardware APIs:

```python
# backend/app/hardware/suruga_seiki.py
class SurugaSeikiClient(BaseHardwareClient):
    async def move_absolute(self, axis: int, position: float, speed: float) -> Result[None, str]:
        result = await self._post("/motion/move_absolute", json={...})
        return Ok(None) if result.is_ok() else Err(result.error)

# backend/app/hardware/exfo_ctp10.py
class ExfoCTP10Client(BaseHardwareClient):
    async def measure(self, calibrate: bool = True) -> Result[MeasurementData, str]:
        result = await self._post("/measure", json={"calibrate": calibrate})
        return Ok(MeasurementData(...)) if result.is_ok() else Err(result.error)
```

The controller only knows:
- "I need to move stage to position X" → POST to Suruga API
- "I need to measure spectrum" → POST to EXFO API

It doesn't care about .NET interop, VISA drivers, or SCPI commands. **Encapsulation.**

## Local Development Setup

### Option 1: Manual Start (Three Terminals)

**Terminal 1 - Suruga Seiki API:**
```bash
cd C:\Users\pic_s\git\probe-flow\instruments\suruga_seiki_ew51
fastapi dev main.py  # Runs on :8001
```

**Terminal 2 - EXFO CTP10 API:**
```bash
cd C:\Users\pic_s\git\exfo-ctp10-api
fastapi dev main.py  # Runs on :8002
```

**Terminal 3 - Measurement Control:**
```bash
cd C:\Users\pic_s\git\zero-db
docker compose watch  # Runs on :8000
```

### Option 2: Docker Compose (Recommended)

Add to `zero-db/docker-compose.override.yml`:

```yaml
services:
  suruga-api:
    build:
      context: ../probe-flow/instruments/suruga_seiki_ew51
    ports:
      - "8001:8000"
    networks:
      - default
    environment:
      - SURUGA_CONNECTION_STRING=...

  exfo-api:
    build:
      context: ../exfo-ctp10-api
    ports:
      - "8002:8000"
    networks:
      - default
    devices:
      - "/dev/usbtmc0:/dev/usbtmc0"  # VISA device passthrough
    environment:
      - EXFO_VISA_ADDRESS=TCPIP0::192.168.1.100::INSTR
```

Then:
```bash
cd C:\Users\pic_s\git\zero-db
docker compose up -d
# All three services start together
```

## Configuration

### Environment Variables

In `zero-db/.env`:
```env
# Hardware API endpoints
SURUGA_SEIKI_URL=http://localhost:8001
EXFO_CTP10_URL=http://localhost:8002

# Or for production
SURUGA_SEIKI_URL=http://probe-station-pc:8001
EXFO_CTP10_URL=http://vector-analyzer-pc:8002
```

### Dependency Injection

The measurement controller receives hardware URLs via configuration:

```python
# In measurement controller
controller = MeasurementController(
    MeasurementConfig(
        order_id="12345",
        devices=[...],
        suruga_base_url=settings.SURUGA_SEIKI_URL,
        exfo_base_url=settings.EXFO_CTP10_URL,
    )
)
```

Hardware clients are created as context managers:
```python
async with SurugaSeikiClient(config.suruga_base_url) as suruga, \
           ExfoCTP10Client(config.exfo_base_url) as exfo:
    # Use clients
```

## API Contracts

### Health Check (All Services)
```http
GET /health
Response: {"status": "ok", "connected": true}
```

### Suruga Seiki API
```http
POST /motion/move_absolute
Body: {"axis_number": 1, "position_um": 1000.0, "speed_um_per_s": 100.0}
Response: {"success": true}

POST /alignment/flat
Body: {AlignmentRequest}
Response: {AlignmentResponse with profiles and power}

GET /position/{axis_number}
Response: {"position_um": 1234.5, "moving": false, "servo_on": true}

GET /io/power/{channel}
Response: {"power": -25.3}
```

### EXFO CTP10 API
```http
POST /configure
Body: {"start_wavelength_nm": 1520, "stop_wavelength_nm": 1580, ...}
Response: {"success": true}

POST /calibrate
Body: {"channels": ["S11", "S21"]}
Response: {"success": true}

POST /measure
Body: {"calibrate": true}
Response: {
  "wavelength_nm": [1520.0, 1520.1, ...],
  "s11_db": [-30.2, -29.8, ...],
  "s21_db": [-3.1, -3.0, ...]
}

GET /power/S21
Response: {"power_dbm": -25.3}
```

## Error Handling

Hardware APIs return HTTP status codes:
- `200` - Success
- `500` - Hardware error (servo not ready, alignment failed, etc.)
- `422` - Invalid parameters

The measurement controller wraps responses in `Result[T, E]`:
```python
result = await suruga.move_absolute(1, 1000.0, 100.0)
if result.is_ok():
    # Continue
else:
    # Emit error event, decide to retry or skip device
    yield ErrorOccurred.now(error=result.error, device_index=i, operation="move")
```

## Testing Strategy

### Unit Tests
Each repo has its own unit tests:
- **Suruga API:** Mock .NET DLL calls
- **EXFO API:** Mock Pymeasure instrument
- **Measurement Control:** Mock hardware HTTP clients

### Integration Tests
Measurement control integration tests:
1. Start mock HTTP servers (FastAPI TestClient)
2. Return predefined responses
3. Test orchestration logic without real hardware

### End-to-End Tests
With real hardware:
1. Start all three services
2. Run measurement via API
3. Verify hardware moves and data is collected

## Migration from Legacy Code

### Legacy Architecture
```
measurement-control-logic/
└── control.py
    ├── ProbeStationAPI (thin HTTP wrapper)
    ├── VectorAnalyzerAPI (thin HTTP wrapper)
    └── AutomaticControl.__enter__() [992 lines]
        ├─ Direct API calls
        ├─ Complex nested logic
        └─ No pause/cancel support
```

### New Architecture
```
zero-db/
└── backend/app/
    ├── hardware/
    │   ├── suruga_seiki.py (rich async client)
    │   └── exfo_ctp10.py (rich async client)
    └── services/
        └── controller.py
            ├─ Async generator (~50 line methods)
            ├─ State machine transitions
            ├─ Progress event streaming
            └─ Pause/cancel/resume support
```

**Key improvements:**
- Thin HTTP wrappers → Rich async clients with Result types
- 992-line method → Modular async generator
- Blocking calls → Async/await non-blocking
- Print statements → Typed progress events
- No control → Pause/resume/cancel

## Future Considerations

### Additional Hardware
If you add new instruments (e.g., thermal controllers, power supplies):
1. Create new repo with FastAPI wrapper
2. Add async client to `backend/app/hardware/`
3. Use in measurement controller

### Hardware Mocking
For development without hardware:
1. Create `mock-hardware-apis` repo
2. Implement same endpoints
3. Return synthetic data
4. Point measurement control to mock URLs

### Load Balancing
If multiple probe stations:
1. Deploy multiple Suruga API instances
2. Add load balancer in front
3. Measurement control connects to load balancer URL

## Related Documents

- [CLAUDE.md](../CLAUDE.md) - Development guide for measurement control system
- [probe-flow README](../../probe-flow/instruments/suruga_seiki_ew51/README.md) - Suruga Seiki API documentation
- [exfo-ctp10-api README](../../exfo-ctp10-api/README.md) - EXFO CTP10 API documentation (to be created)

## Decision Status

**Status:** Accepted
**Date:** 2025-01-07
**Author:** Claude Code + User
**Reviewers:** N/A

This decision aligns with the existing Suruga Seiki API pattern and leverages proven microservices principles for hardware control systems.
