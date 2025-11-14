# Zero-DB Development Guide

This guide will help you develop and test the Zero-DB application in development mode on the `dev` branch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Development Modes](#development-modes)
4. [Testing Your Changes](#testing-your-changes)
5. [Git Workflow (dev branch)](#git-workflow-dev-branch)
6. [Common Development Tasks](#common-development-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting development, ensure you have the following installed:

### Required Tools

- **Docker Desktop** (latest version)
  - Download: https://www.docker.com/products/docker-desktop
  - Verify: `docker --version` and `docker compose version`

- **Python 3.10+** with UV package manager
  - Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Verify: `uv --version`

- **Node.js 18+** with npm
  - Install via fnm (recommended): `brew install fnm` (macOS) or see https://github.com/Schniz/fnm
  - Verify: `node --version` and `npm --version`

### Optional Tools

- **PostgreSQL client** (for database inspection)
  - macOS: `brew install postgresql@17`
  - Verify: `psql --version`

- **websocat** (for WebSocket debugging)
  - macOS: `brew install websocat`
  - Verify: `websocat --version`

---

## Initial Setup

### 1. Clone and Navigate to Project

```bash
# If not already cloned
git clone https://github.com/yourusername/zero-db.git
cd zero-db

# Switch to dev branch
git checkout dev
git pull origin dev
```

### 2. Environment Configuration

The `.env` file is already configured for local development. You can review it:

```bash
cat .env
```

**Key settings for development:**
- `DOMAIN=localhost` (for basic local development)
- `FRONTEND_HOST=http://localhost:5173` (Vite dev server)
- `ENVIRONMENT=local`
- `POSTGRES_SERVER=localhost` (when running backend locally outside Docker)

**Important:** Never commit secrets to Git. The default passwords are for local development only.

### 3. Install Backend Dependencies (Optional - for local development)

```bash
cd backend
uv sync
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate  # Windows
cd ..
```

### 4. Install Frontend Dependencies (Optional - for local development)

```bash
cd frontend
npm install
cd ..
```

---

## Development Modes

You have **three main options** for development:

### Option 1: Full Docker Stack with Live Reload (Recommended for Full-Stack Testing)

This runs everything in Docker containers with automatic code reloading.

**Start the stack:**
```bash
docker compose watch
```

**What happens:**
- PostgreSQL database starts on port `5432`
- Adminer (DB UI) starts on `http://localhost:8080`
- Backend API starts on `http://localhost:8000` with auto-reload
- Frontend starts on `http://localhost:5173` (development build)
- Mailcatcher (email testing) on `http://localhost:1080`

**Access the application:**
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs
- Adminer (DB): http://localhost:8080
- Mailcatcher: http://localhost:1080

**Watch logs:**
```bash
docker compose logs -f              # All services
docker compose logs -f backend      # Backend only
docker compose logs -f frontend     # Frontend only
```

**Stop the stack:**
```bash
Ctrl+C  # Stop watching
docker compose down  # Stop containers
docker compose down -v  # Stop and remove volumes (database data)
```

### Option 2: Docker Backend + Local Frontend (Recommended for Frontend Development)

Run backend in Docker, but frontend locally for faster hot-reload.

**Terminal 1: Start backend services**
```bash
docker compose up db backend adminer mailcatcher
```

**Terminal 2: Start frontend locally**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173 (Vite dev server - very fast reload)
- Backend API: http://localhost:8000/docs
- Adminer: http://localhost:8080

**Why this approach?**
- Frontend hot-reload is instant (< 100ms)
- No Docker overhead for frontend development
- Backend still runs in consistent environment

### Option 3: Everything Local (Advanced - for Backend Development)

Run both backend and frontend outside Docker.

**Terminal 1: Start PostgreSQL**
```bash
docker compose up db
```

**Terminal 2: Start backend**
```bash
cd backend
uv sync
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run database migrations
alembic upgrade head

# Start FastAPI dev server
fastapi dev app/main.py
```

**Terminal 3: Start frontend**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

**Why this approach?**
- Direct debugging with breakpoints in IDE
- Faster iteration for backend development
- Full control over Python environment

---

## Testing Your Changes

### Visual Verification

After making changes (favicon, logo, colors), verify them:

**1. Open the application:**
```bash
# If using Docker:
docker compose watch

# Wait for services to start, then open:
# http://localhost:5173
```

**2. Check branding changes:**
- **Favicon:** Look at the browser tab icon (should be Zero-DB favicon)
- **Logo:** Check login page, signup page, and navbar (should be Zero-DB logo)
- **Colors:** Links and main UI elements should be light orange (#FF9966) instead of green

**3. Test login flow:**
```
Email: admin@example.com
Password: changethis
```

**4. Navigate the dashboard:**
- Check that orange color appears in links
- Verify logo in navbar
- Test creating items, user settings, etc.

### Backend Testing

Run the test suite:

```bash
# Using Docker:
docker compose exec backend bash scripts/tests-start.sh

# Or run locally:
cd backend
source .venv/bin/activate
bash ./scripts/test.sh

# With pytest options:
docker compose exec backend bash scripts/tests-start.sh -x  # Stop on first error
docker compose exec backend bash scripts/tests-start.sh -v  # Verbose output
```

**Test coverage:**
```bash
cd backend
source .venv/bin/activate
coverage run -m pytest
coverage report
coverage html  # Generate HTML report in htmlcov/index.html
```

### Frontend Testing

**Linting:**
```bash
cd frontend
npm run lint
```

**End-to-end tests (Playwright):**
```bash
# Start backend first
docker compose up -d backend

# Run tests
cd frontend
npx playwright test

# Run tests in UI mode (interactive)
npx playwright test --ui
```

### Database Inspection

**Using Adminer (GUI):**
1. Open http://localhost:8080
2. Login:
   - System: PostgreSQL
   - Server: db (or localhost if running outside Docker)
   - Username: postgres
   - Password: changethis
   - Database: app

**Using psql (CLI):**
```bash
# Connect to Docker database
docker compose exec db psql -U postgres -d app

# Or connect to local database
psql -h localhost -U postgres -d app

# Useful commands:
\dt          # List tables
\d+ user     # Describe user table
SELECT * FROM "user" LIMIT 5;
\q           # Quit
```

---

## Git Workflow (dev branch)

To avoid conflicts with the master branch:

### Create a Feature Branch from dev

```bash
# Ensure you're on dev and up to date
git checkout dev
git pull origin dev

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes...
git add .
git commit -m "feat: add your feature description"

# Push to remote
git push origin feature/your-feature-name
```

### Keep dev in Sync

```bash
# Switch to dev
git checkout dev

# Pull latest changes
git pull origin dev

# Merge dev into your feature branch
git checkout feature/your-feature-name
git merge dev

# Resolve any conflicts, then:
git push origin feature/your-feature-name
```

### Merge Feature into dev

```bash
# When your feature is complete and tested:
git checkout dev
git pull origin dev
git merge feature/your-feature-name

# Test thoroughly, then:
git push origin dev
```

**Never merge dev directly into master** without proper testing and approval.

---

## Common Development Tasks

### Add a New API Endpoint

1. **Define the endpoint** in `backend/app/api/routes/<module>.py`:
   ```python
   @router.get("/my-endpoint")
   def my_endpoint() -> dict:
       return {"message": "Hello"}
   ```

2. **Add tests** in `backend/tests/api/routes/test_<module>.py`:
   ```python
   def test_my_endpoint(client):
       response = client.get("/api/v1/my-endpoint")
       assert response.status_code == 200
   ```

3. **Regenerate frontend client**:
   ```bash
   # Backend must be running
   cd frontend
   npm run generate-client
   ```

### Add a Database Model

1. **Define model** in `backend/app/models.py`:
   ```python
   class MyModel(SQLModel, table=True):
       id: int | None = Field(default=None, primary_key=True)
       name: str
   ```

2. **Create migration**:
   ```bash
   docker compose exec backend bash
   alembic revision --autogenerate -m "Add MyModel"
   # Review the migration file
   alembic upgrade head
   exit
   ```

3. **Add CRUD operations** in `backend/app/crud.py`

4. **Create API endpoints** as above

### Add a Frontend Route

1. **Create route file** in `frontend/src/routes/<route-name>.tsx`:
   ```tsx
   import { createFileRoute } from "@tanstack/react-router"

   export const Route = createFileRoute("/<route-name>")({
     component: MyComponent,
   })

   function MyComponent() {
     return <div>My Component</div>
   }
   ```

2. **TanStack Router** auto-detects the route (file-based routing)

3. **Use generated API client** from `frontend/src/client/`

### Update Theme Colors

Edit `frontend/src/theme.tsx`:
```tsx
theme: {
  tokens: {
    colors: {
      ui: {
        main: { value: "#FF9966" }, // Your custom color
      },
    },
  },
},
```

### Change Logo/Favicon

1. **Place image** in `frontend/public/assets/images/`
2. **Update references**:
   - Favicon: `frontend/index.html`
   - Logo: `frontend/src/routes/login.tsx`, `signup.tsx`, `components/Common/Navbar.tsx`

---

## Troubleshooting

### "Port already in use" error

```bash
# Find process using port 8000 (backend)
lsof -i :8000
kill -9 <PID>

# Or stop all Docker containers
docker compose down
```

### Frontend can't connect to backend

**Check CORS settings** in `.env`:
```bash
BACKEND_CORS_ORIGINS="http://localhost,http://localhost:5173,https://localhost,https://localhost:5173"
```

**Verify backend is running:**
```bash
curl http://localhost:8000/api/v1/utils/health-check/
```

### Database migrations not applying

```bash
# Check migration status
docker compose exec backend alembic current

# Apply migrations
docker compose exec backend alembic upgrade head

# If stuck, downgrade and re-apply
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic upgrade head
```

### "Module not found" in frontend

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Docker containers unhealthy

```bash
# Check container status
docker compose ps

# View logs for unhealthy service
docker compose logs backend

# Restart service
docker compose restart backend

# Nuclear option: rebuild
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Hot reload not working

**Backend:**
- Ensure using `docker compose watch` or `fastapi run --reload`
- Check file is not in `.dockerignore`

**Frontend:**
- Vite should auto-reload
- Check browser console for errors
- Try hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### Can't login with admin credentials

**Reset superuser:**
```bash
docker compose exec backend bash
python -c "
from app.core.db import engine
from app.models import User
from app.core.security import get_password_hash
from sqlmodel import Session, select

with Session(engine) as session:
    user = session.exec(select(User).where(User.email == 'admin@example.com')).first()
    if user:
        user.hashed_password = get_password_hash('changethis')
        session.add(user)
        session.commit()
        print('Password reset to: changethis')
"
exit
```

---

## Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Start full stack | `docker compose watch` |
| Stop stack | `Ctrl+C` then `docker compose down` |
| View logs | `docker compose logs -f` |
| Restart service | `docker compose restart <service>` |
| Access backend shell | `docker compose exec backend bash` |
| Access database | `docker compose exec db psql -U postgres -d app` |
| Run backend tests | `docker compose exec backend bash scripts/tests-start.sh` |
| Run frontend dev | `cd frontend && npm run dev` |
| Generate API client | `cd frontend && npm run generate-client` |
| Database migration | `docker compose exec backend alembic upgrade head` |

### Service Ports

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://localhost:5173 | 5173 |
| Backend API | http://localhost:8000 | 8000 |
| API Docs | http://localhost:8000/docs | 8000 |
| Adminer (DB UI) | http://localhost:8080 | 8080 |
| Mailcatcher | http://localhost:1080 | 1080 |
| PostgreSQL | localhost:5432 | 5432 |

### Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Admin User | admin@example.com | changethis |
| PostgreSQL | postgres | changethis |
| Adminer | postgres | changethis |

---

## Next Steps

Now that your development environment is set up with Zero-DB branding:

1. **Verify the changes** by running the application
2. **Explore the codebase** structure (see CLAUDE.md)
3. **Start building measurement control features** (see CLAUDE.md "Measurement Control System" section)
4. **Integrate microservices** when ready (Suruga Seiki and EXFO CTP10 APIs)

Happy coding! 🚀
