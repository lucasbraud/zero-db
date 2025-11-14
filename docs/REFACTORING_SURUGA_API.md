# Refactoring Plan: suruga-seiki-ew51-api

## Goal

Extract Suruga Seiki EW51 code from `probe-flow` monorepo into a clean, standalone `suruga-seiki-ew51-api` repository that:
- Follows FastAPI standard structure
- Uses `uv` for dependency management (matching `zero-db`)
- Contains only what's needed for the Suruga API
- Serves as a template for `exfo-ctp10-api`

## Current State

**Location:** `C:\Users\pic_s\git\probe-flow\instruments\suruga_seiki_ew51\`

**Structure:**
```
suruga_seiki_ew51/
├── daemon/
│   └── app/                  # FastAPI application
│       ├── dll/              # .NET DLLs (8 files, ~7MB)
│       ├── routers/          # 9 router files (909 LOC)
│       ├── main.py           # 294 lines
│       ├── controller_manager.py  # 2262 lines
│       ├── models.py         # 825 lines
│       ├── config.py         # 80 lines
│       └── dependencies.py
├── examples/                 # Test scripts
├── docs/                     # PDF manual
└── tests/
```

**Dependencies:** Poetry (pyproject.toml + poetry.lock)

**Issues:**
- Nested `daemon/app/` structure (non-standard)
- Poetry instead of uv
- Includes unused dependencies (database, cloud storage)
- Part of larger monorepo

## Target State

**Location:** `C:\Users\pic_s\git\suruga-seiki-ew51-api\`

**Structure:**
```
suruga-seiki-ew51-api/
├── app/                      # FastAPI application (un-nested)
│   ├── dll/                  # .NET DLLs
│   ├── routers/              # API endpoints
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── servo.py
│   │   ├── motion.py
│   │   ├── position.py
│   │   ├── alignment.py
│   │   ├── profile.py
│   │   ├── angle_adjustment.py
│   │   ├── io.py
│   │   └── websocket.py
│   ├── main.py               # Entry point
│   ├── controller_manager.py # .NET DLL wrapper
│   ├── models.py             # Pydantic models
│   ├── config.py             # Settings
│   └── dependencies.py       # DI helpers
├── examples/                 # Test scripts (keep)
│   ├── test_flat_alignment.py
│   ├── test_profile_measurement.py
│   └── test_angle_adjustment.py
├── tests/                    # Unit tests
│   └── test_controller.py
├── docs/                     # Documentation
│   └── DA1000_DA1100_Manual.pdf
├── scripts/                  # Utility scripts
│   └── manual_control.py     # Terminal UI
├── pyproject.toml            # uv configuration
├── uv.lock                   # Locked dependencies
├── README.md                 # Clean standalone docs
├── Dockerfile                # Container build
├── .gitignore
└── LICENSE
```

**Dependencies:** uv (pyproject.toml + uv.lock)

## Refactoring Steps

### Step 1: Create New Repository

```bash
cd C:\Users\pic_s\git
mkdir suruga-seiki-ew51-api
cd suruga-seiki-ew51-api
git init
```

### Step 2: Copy Core Files

**Copy from probe-flow:**
```bash
# From C:\Users\pic_s\git\probe-flow\instruments\suruga_seiki_ew51\

# Core application (un-nest daemon/app → app)
cp -r daemon/app ./app

# Examples (useful for testing)
cp -r examples ./examples

# Documentation
mkdir docs
cp docs/AG23-0016-003E_DA1000_DA1100_Software_Reference_manual_EN.pdf ./docs/

# Test scripts
mkdir scripts
cp ../../scripts/manual_control.py ./scripts/

# Tests (if any)
cp -r tests ./tests
```

### Step 3: Create uv-based pyproject.toml

**New file:** `pyproject.toml`

```toml
[project]
name = "suruga-seiki-ew51-api"
version = "1.0.0"
description = "FastAPI server for Suruga Seiki EW51 probe station control"
readme = "README.md"
requires-python = ">=3.10,<4.0"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "websockets>=12.0",
    "python-multipart>=0.0.6",
    "pythonnet>=3.0.3",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "python-json-logger>=2.0.7",
    "colorlog>=6.8.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.1",
    "ruff>=0.2.2",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Step 4: Update Imports

**Before (nested structure):**
```python
from instruments.suruga_seiki_ew51.daemon.app.controller_manager import SurugaSeikiController
from instruments.suruga_seiki_ew51.daemon.app.models import MoveAbsoluteRequest
```

**After (flat structure):**
```python
from app.controller_manager import SurugaSeikiController
from app.models import MoveAbsoluteRequest
```

**Files to update:**
- All files in `app/routers/`
- `app/main.py`
- `app/dependencies.py`
- Test files
- Example scripts

**Search and replace:**
```bash
# Use editor or script
find app/ -name "*.py" -exec sed -i \
  's/from instruments\.suruga_seiki_ew51\.daemon\.app\./from app./g' {} \;
```

### Step 5: Update main.py Entry Point

**Before:**
```python
# Complex Poetry script entry point
def run():
    import uvicorn
    uvicorn.run("instruments.suruga_seiki_ew51.daemon.app.main:app", ...)
```

**After:**
```python
# Standard FastAPI pattern
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
```

### Step 6: Create README.md

**New file:** `README.md`

```markdown
# Suruga Seiki EW51 Probe Station API

FastAPI server for controlling Suruga Seiki DA1000/DA1100 probe stations via .NET DLL interop.

## Features

- 12-axis motion control (single/2D/3D interpolation)
- Optical alignment (flat 2D, focus 3D)
- Profile measurement scanning
- Angle adjustment (DA1100 only)
- I/O control (contact sensors, power meters)
- Real-time WebSocket streaming
- Health monitoring with auto-reconnection

## Requirements

- Python 3.10+
- Windows (for .NET DLL support via pythonnet)
- Suruga Seiki DA1000 or DA1100 hardware

## Installation

### Using uv (recommended)

\`\`\`bash
# Install uv if not already installed
pip install uv

# Clone repository
git clone <repo-url>
cd suruga-seiki-ew51-api

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
\`\`\`

### Using pip

\`\`\`bash
pip install -e .
\`\`\`

## Usage

### Start API Server

\`\`\`bash
# Development mode (with auto-reload)
fastapi dev app/main.py

# Production mode
fastapi run app/main.py --host 0.0.0.0 --port 8001
\`\`\`

Server runs on: http://localhost:8001

### API Documentation

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **OpenAPI JSON:** http://localhost:8001/openapi.json

### Example Usage

\`\`\`python
import httpx

async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
    # Turn on servo
    await client.post("/servo/turn_on", json={"axis_number": 1})

    # Move to position
    await client.post("/motion/move_absolute", json={
        "axis_number": 1,
        "position_um": 1000.0,
        "speed_um_per_s": 100.0
    })

    # Get position
    response = await client.get("/position/1")
    print(response.json())
\`\`\`

See `examples/` directory for more detailed usage examples.

## Configuration

Environment variables (`.env` file or system):

\`\`\`env
# Hardware connection
SURUGA_AUTO_CONNECT=true
SURUGA_CONNECTION_STRING=<your-connection-string>

# API settings
API_HOST=0.0.0.0
API_PORT=8001

# Logging
LOG_LEVEL=INFO
\`\`\`

## Development

\`\`\`bash
# Install with dev dependencies
uv sync

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
ruff format app/

# Lint code
ruff check app/

# Type check
mypy app/
\`\`\`

## API Endpoints

### Connection
- `POST /connect` - Connect to hardware
- `POST /disconnect` - Disconnect from hardware
- `GET /connection/status` - Connection status

### Servo Control
- `POST /servo/turn_on` - Turn on single servo
- `POST /servo/turn_off` - Turn off single servo
- `POST /servo/turn_on_servos_batch` - Turn on multiple servos
- `POST /servo/wait_for_axes_ready_batch` - Wait for servos ready

### Motion
- `POST /motion/move_absolute` - Absolute move
- `POST /motion/move_relative` - Relative move
- `POST /motion/move_2d_absolute` - 2D interpolation
- `POST /motion/move_3d_absolute` - 3D interpolation
- `POST /motion/emergency_stop` - Stop all axes

### Position
- `GET /position/{axis_number}` - Single axis position
- `GET /position/all` - All axes positions

### Alignment
- `POST /alignment/flat` - 2D flat alignment
- `POST /alignment/focus` - 3D focus alignment

### Profile
- `POST /profile/measure` - Profile measurement scan

### Angle Adjustment (DA1100)
- `POST /angle_adjustment/execute` - Angle adjustment

### I/O
- `POST /io/set_digital_output` - Set digital output
- `GET /io/analog_input/{channel}` - Read analog input
- `GET /io/power/{channel}` - Read power meter

### WebSocket
- `WS /ws/position_stream` - Real-time position streaming

## Docker

\`\`\`bash
# Build image
docker build -t suruga-api .

# Run container
docker run -p 8001:8001 suruga-api
\`\`\`

## License

MIT

## Related Projects

- [zero-db](https://github.com/.../zero-db) - Measurement control system using this API
- [exfo-ctp10-api](https://github.com/.../exfo-ctp10-api) - EXFO vector analyzer API
\`\`\`

### Step 7: Create Dockerfile

**New file:** `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Run server
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8001"]
```

### Step 8: Create .gitignore

**New file:** `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/
ENV/

# uv
uv.lock

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Environment
.env
.env.local

# Logs
*.log

# OS
.DS_Store
Thumbs.db
```

### Step 9: Install and Test

```bash
# From new repo root
cd C:\Users\pic_s\git\suruga-seiki-ew51-api

# Install dependencies
uv sync

# Activate environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run server
fastapi dev app/main.py

# In another terminal, test
curl http://localhost:8001/docs
```

### Step 10: Update Measurement Control

Update `zero-db` to point to new repo:

**In docker-compose.override.yml:**
```yaml
services:
  suruga-api:
    build:
      context: ../suruga-seiki-ew51-api  # Updated path
    ports:
      - "8001:8001"
```

**In backend .env:**
```env
SURUGA_SEIKI_URL=http://localhost:8001
```

## Removed Dependencies

These were in original `probe-flow` but not needed for standalone Suruga API:

**Database:**
- sqlalchemy
- aiomysql
- alembic

**Cloud Storage:**
- boto3 (AWS S3)
- google-cloud-storage

**HTTP Clients (unless used):**
- httpx (only needed for client calls)
- aiohttp

**File Operations:**
- aiofiles (unless async file ops are used)

**Utilities:**
- python-dateutil
- pytz
- pyyaml

## Migration Checklist

- [ ] Create new repository
- [ ] Copy core files (un-nest structure)
- [ ] Create uv-based pyproject.toml
- [ ] Update all imports
- [ ] Update main.py entry point
- [ ] Create README.md
- [ ] Create Dockerfile
- [ ] Create .gitignore
- [ ] Test `uv sync` works
- [ ] Test API server starts
- [ ] Test API endpoints (use examples/)
- [ ] Update zero-db docker-compose to point to new repo
- [ ] Test integration with measurement control
- [ ] Commit and push new repo
- [ ] Update probe-flow README to point to new repo
- [ ] Archive or delete old probe-flow repo (optional)

## Post-Refactoring

After successful refactoring, this clean structure serves as a **template for exfo-ctp10-api**:

```bash
# Create EXFO API based on Suruga template
cp -r suruga-seiki-ew51-api exfo-ctp10-api
cd exfo-ctp10-api

# Update:
# - Replace controller_manager.py with Pymeasure wrapper
# - Update routers for EXFO operations
# - Update models for EXFO requests/responses
# - Update README
```

## Benefits of Refactoring

1. **Clean separation** - Standalone repo, no monorepo coupling
2. **Standard structure** - Matches FastAPI best practices
3. **Modern tooling** - uv instead of Poetry (consistency with zero-db)
4. **Minimal dependencies** - Only what's needed
5. **Template ready** - Perfect blueprint for EXFO API
6. **Docker-ready** - Easy containerization
7. **Well-documented** - Clear README for new developers

## Notes

- Keep DLLs in `app/dll/` - they're ~7MB but essential
- Keep examples/ - useful for testing and documentation
- Manual control script is helpful for debugging
- WebSocket streaming is a key feature - preserve it
- Health monitoring with auto-reconnection should remain
