"""
Automated script to refactor probe-flow Suruga Seiki API into standalone repo.

This script:
1. Creates new suruga-seiki-ew51-api directory
2. Copies necessary files from probe-flow
3. Un-nests daemon/app structure
4. Updates imports
5. Creates new configuration files

Usage:
    python scripts/refactor_suruga_api.py
"""

import os
import shutil
import re
from pathlib import Path


def main():
    """Execute refactoring steps."""
    print("=" * 80)
    print("Suruga Seiki EW51 API Refactoring Script")
    print("=" * 80)
    print()

    # Paths
    git_root = Path(r"C:\Users\pic_s\git")
    probe_flow_root = git_root / "probe-flow"
    suruga_old = probe_flow_root / "instruments" / "suruga_seiki_ew51"
    suruga_new = git_root / "suruga-seiki-ew51-api"

    # Check source exists
    if not suruga_old.exists():
        print(f"❌ Source not found: {suruga_old}")
        print(f"   Please check probe-flow is at: {probe_flow_root}")
        return

    # Check target doesn't exist
    if suruga_new.exists():
        response = input(
            f"⚠️  Target already exists: {suruga_new}\n   Delete and recreate? (y/n): "
        )
        if response.lower() == "y":
            shutil.rmtree(suruga_new)
            print(f"   Deleted {suruga_new}")
        else:
            print("   Aborted.")
            return

    print(f"📂 Source: {suruga_old}")
    print(f"📂 Target: {suruga_new}")
    print()

    # Step 1: Create new repo structure
    print("Step 1: Creating new repository structure...")
    suruga_new.mkdir(parents=True, exist_ok=True)

    # Step 2: Copy core application (un-nest daemon/app → app)
    print("Step 2: Copying core application files...")
    app_old = suruga_old / "daemon" / "app"
    app_new = suruga_new / "app"

    if app_old.exists():
        shutil.copytree(app_old, app_new)
        print(f"   ✓ Copied {app_old} → {app_new}")
    else:
        print(f"   ❌ Source app not found: {app_old}")
        return

    # Step 3: Copy examples
    print("Step 3: Copying examples...")
    examples_old = suruga_old / "examples"
    examples_new = suruga_new / "examples"
    if examples_old.exists():
        shutil.copytree(examples_old, examples_new)
        print(f"   ✓ Copied examples")
    else:
        print(f"   ⚠️  Examples not found")

    # Step 4: Copy docs
    print("Step 4: Copying documentation...")
    docs_new = suruga_new / "docs"
    docs_new.mkdir(exist_ok=True)

    pdf_old = (
        suruga_old
        / "docs"
        / "AG23-0016-003E_DA1000_DA1100_Software_Reference_manual_EN.pdf"
    )
    if pdf_old.exists():
        shutil.copy(pdf_old, docs_new)
        print(f"   ✓ Copied PDF manual")
    else:
        print(f"   ⚠️  PDF manual not found")

    # Step 5: Copy scripts
    print("Step 5: Copying utility scripts...")
    scripts_new = suruga_new / "scripts"
    scripts_new.mkdir(exist_ok=True)

    manual_control_old = probe_flow_root / "scripts" / "manual_control.py"
    if manual_control_old.exists():
        shutil.copy(manual_control_old, scripts_new)
        print(f"   ✓ Copied manual_control.py")
    else:
        print(f"   ⚠️  manual_control.py not found")

    # Step 6: Copy tests
    print("Step 6: Copying tests...")
    tests_old = suruga_old / "tests"
    tests_new = suruga_new / "tests"
    if tests_old.exists():
        shutil.copytree(tests_old, tests_new)
        print(f"   ✓ Copied tests")
    else:
        print(f"   ℹ️  No tests directory")

    # Step 7: Update imports
    print("Step 7: Updating imports...")
    update_imports(app_new)
    print(f"   ✓ Updated imports in app/")

    if examples_new.exists():
        update_imports(examples_new)
        print(f"   ✓ Updated imports in examples/")

    if (scripts_new / "manual_control.py").exists():
        update_imports(scripts_new)
        print(f"   ✓ Updated imports in scripts/")

    # Step 8: Create pyproject.toml
    print("Step 8: Creating pyproject.toml...")
    create_pyproject_toml(suruga_new)
    print(f"   ✓ Created pyproject.toml")

    # Step 9: Create README.md
    print("Step 9: Creating README.md...")
    create_readme(suruga_new)
    print(f"   ✓ Created README.md")

    # Step 10: Create Dockerfile
    print("Step 10: Creating Dockerfile...")
    create_dockerfile(suruga_new)
    print(f"   ✓ Created Dockerfile")

    # Step 11: Create .gitignore
    print("Step 11: Creating .gitignore...")
    create_gitignore(suruga_new)
    print(f"   ✓ Created .gitignore")

    # Step 12: Initialize git
    print("Step 12: Initializing git repository...")
    os.chdir(suruga_new)
    os.system("git init")
    print(f"   ✓ Initialized git")

    print()
    print("=" * 80)
    print("✅ Refactoring complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print(f"1. cd {suruga_new}")
    print("2. uv sync")
    print("3. source .venv/bin/activate  (or .venv\\Scripts\\activate on Windows)")
    print("4. fastapi dev app/main.py")
    print("5. Test API at http://localhost:8001/docs")
    print()


def update_imports(directory: Path):
    """
    Update imports from old nested structure to new flat structure.

    Changes:
        from instruments.suruga_seiki_ew51.daemon.app.X → from app.X
    """
    old_pattern = re.compile(
        r"from\s+instruments\.suruga_seiki_ew51\.daemon\.app\.(\w+)"
    )
    new_replacement = r"from app.\1"

    for py_file in directory.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            updated_content = old_pattern.sub(new_replacement, content)

            if updated_content != content:
                py_file.write_text(updated_content, encoding="utf-8")
                print(f"      Updated: {py_file.relative_to(directory.parent)}")
        except Exception as e:
            print(f"      ⚠️  Failed to update {py_file}: {e}")


def create_pyproject_toml(repo_root: Path):
    """Create uv-based pyproject.toml."""
    content = '''[project]
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
'''
    (repo_root / "pyproject.toml").write_text(content, encoding="utf-8")


def create_readme(repo_root: Path):
    """Create README.md."""
    content = """# Suruga Seiki EW51 Probe Station API

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

```bash
# Install uv
pip install uv

# Clone repository
git clone <repo-url>
cd suruga-seiki-ew51-api

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\\Scripts\\activate     # Windows
```

## Usage

```bash
# Development mode
fastapi dev app/main.py

# Production mode
fastapi run app/main.py --host 0.0.0.0 --port 8001
```

Server runs on: http://localhost:8001

API Documentation:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

## Configuration

Create `.env` file:

```env
SURUGA_AUTO_CONNECT=true
SURUGA_CONNECTION_STRING=<your-connection-string>
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=INFO
```

## Development

```bash
# Run tests
pytest

# Format code
ruff format app/

# Lint code
ruff check app/

# Type check
mypy app/
```

## Docker

```bash
# Build
docker build -t suruga-api .

# Run
docker run -p 8001:8001 suruga-api
```

## API Endpoints

See `/docs` for full API documentation.

### Key Endpoints:
- `POST /connect` - Connect to hardware
- `POST /servo/turn_on` - Activate servo
- `POST /motion/move_absolute` - Move to position
- `GET /position/{axis}` - Query position
- `POST /alignment/flat` - 2D alignment
- `POST /alignment/focus` - 3D alignment
- `WS /ws/position_stream` - Real-time streaming

## License

MIT

## Related Projects

- [zero-db](https://github.com/.../zero-db) - Measurement control system
- [exfo-ctp10-api](https://github.com/.../exfo-ctp10-api) - EXFO vector analyzer API
"""
    (repo_root / "README.md").write_text(content, encoding="utf-8")


def create_dockerfile(repo_root: Path):
    """Create Dockerfile."""
    content = """FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-dev

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8001

# Run server
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8001"]
"""
    (repo_root / "Dockerfile").write_text(content, encoding="utf-8")


def create_gitignore(repo_root: Path):
    """Create .gitignore."""
    content = """# Python
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
"""
    (repo_root / ".gitignore").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
