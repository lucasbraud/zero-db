# MIRA Integration - Simplified Setup Guide

## Overview

This zero-db project uses **Timofey's `api-auth` and `api-abstraction` packages** for MIRA database integration. This means **NO manual OAuth2 configuration is required** - authentication is handled automatically by the packages.

---

## Prerequisites

1. **Access to GitLab repositories**:
   - `https://gitlab.com/enlightra/mira/authentication/api-auth`
   - `https://gitlab.com/enlightra/mira/packages/api-abstraction`

2. **GitLab Authentication**:
   - Personal Access Token (PAT) or SSH key configured
   - See [GitLab Authentication Setup](#gitlab-authentication-setup) below

---

## Installation Steps

### Step 1: Configure GitLab Authentication

#### Option A: SSH Key (Recommended)
```bash
# Check if you already have SSH configured
ssh -T git@gitlab.com

# If successful, you'll see:
# Welcome to GitLab, @your-username!
```

#### Option B: Personal Access Token
```bash
# Create a PAT at: https://gitlab.com/-/profile/personal_access_tokens
# Scopes needed: read_api, read_repository

# Configure git to use token
git config --global url."https://oauth2:<YOUR_TOKEN>@gitlab.com/".insteadOf "https://gitlab.com/"
```

### Step 2: Install Dependencies

```bash
cd backend
uv sync
```

This will automatically install:
- `api-auth` from GitLab (OAuth2 authentication)
- `api-abstraction` from GitLab (MIRA API wrapper)
- All other dependencies (FastAPI, etc.)

**Expected output:**
```
✓ api-auth @ git+https://gitlab.com/enlightra/mira/authentication/api-auth.git
✓ api-abstraction @ git+https://gitlab.com/enlightra/mira/packages/api-abstraction.git
```

### Step 3: Configure Environment

**Edit `.env` file** (in project root):

```bash
# MIRA Database Configuration
MIRA_BASE_URL=https://mira.enlightra.com              # Production
MIRA_BASE_URL_DEV=https://dev.mira.enlightra.com     # Development
MIRA_CACHE_TTL_SECONDS=1800                           # Cache TTL (30 minutes)
MIRA_MAX_ORDERS_PER_REQUEST=4                         # Max orders per request
MIRA_MEASURER_EMAIL=your.email@enlightra.com         # Your email for tracking
```

**That's it!** No `MIRA_CLIENT_ID`, `MIRA_CLIENT_SECRET`, or other OAuth2 credentials needed.

### Step 4: Start Backend

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
fastapi dev app/main.py
```

**Wait for:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 5: Test MIRA Connection

```bash
# In a new terminal
curl -X GET "http://localhost:8000/api/v1/orders/health"
```

**Expected response:**
```json
{
  "status": "healthy",
  "mira_base_url": "https://dev.mira.enlightra.com",
  "environment": "local"
}
```

---

## How Authentication Works

### Under the Hood

1. **api-auth Package**:
   - Reads OAuth2 credentials from its own configuration
   - Manages token acquisition and refresh automatically
   - Handles retry logic on 401 errors

2. **api-abstraction Package**:
   - Wraps MIRA API endpoints
   - Uses `api-auth` for all requests
   - Provides clean Python interface

3. **zero-db MIRA Client**:
   - Thin wrapper around `api-abstraction`
   - Adds async compatibility
   - Adds file-based caching
   - Adds image processing (GZIP decompression, thumbnails)

### Authentication Flow
```
User Request → FastAPI Endpoint
    ↓
zero-db MIRAClient (mira_client_v2.py)
    ↓
api-abstraction (CombsLinearMeasurements)
    ↓
api-auth (AuthService) → AWS Cognito OAuth2
    ↓
MIRA Database API
```

---

## Troubleshooting

### Issue: "Failed to install api-auth"

**Error:**
```
ERROR: Could not find a version that satisfies the requirement api-auth
```

**Solution:**
1. Verify GitLab authentication (Step 1)
2. Try manual installation:
   ```bash
   cd backend
   uv pip install git+https://gitlab.com/enlightra/mira/authentication/api-auth.git
   ```
3. Check network/firewall: Can you access `gitlab.com`?

### Issue: "ImportError: No module named 'api_auth'"

**Solution:**
```bash
cd backend
source .venv/bin/activate
python -c "import api_auth; print(api_auth.__file__)"
```

If import fails, reinstall:
```bash
uv pip uninstall api-auth api-abstraction
uv sync
```

### Issue: "MIRA health check failed: Authentication failed"

**Cause:** api-auth package OAuth2 credentials not configured correctly

**Solution:**
1. Check if `api-auth` has its own configuration file
2. Contact Timofey or MIRA admin for correct setup
3. Verify you have access to MIRA API (dev or prod)

### Issue: "Failed to get order 123: HTTP 404"

**Cause:** Order doesn't exist in MIRA environment

**Solution:**
1. Verify order ID is correct
2. Check if using correct environment:
   - `ENVIRONMENT=local` → dev MIRA
   - `ENVIRONMENT=production` → prod MIRA
3. Try a known order ID from MIRA UI

---

## GitLab Authentication Setup

### SSH Key Setup (Recommended)

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your.email@enlightra.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitLab:
# 1. Go to https://gitlab.com/-/profile/keys
# 2. Paste public key
# 3. Click "Add key"

# Test connection
ssh -T git@gitlab.com
```

### Personal Access Token Setup

```bash
# 1. Go to: https://gitlab.com/-/profile/personal_access_tokens
# 2. Create token with scopes: read_api, read_repository
# 3. Copy token

# Configure git
git config --global url."https://oauth2:YOUR_TOKEN@gitlab.com/".insteadOf "https://gitlab.com/"

# Or set environment variable for one-time use
export GIT_ASKPASS=echo
export GIT_USERNAME=oauth2
export GIT_PASSWORD=YOUR_TOKEN
```

---

## Differences from Original Implementation

### Before (Manual OAuth2)
```python
# .env
MIRA_CLIENT_ID=56a17up5ouquq9jfep9nbh2a0u
MIRA_CLIENT_SECRET=<your-secret>
MIRA_TOKEN_URL=https://...cognito.com/oauth2/token
MIRA_SCOPE=default-m2m-resource-server-btncxn

# Code
client = httpx.AsyncClient()
token = await get_oauth2_token(client_id, client_secret, ...)
response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
```

### After (api-auth Package)
```python
# .env
# No OAuth2 credentials needed!
MIRA_MEASURER_EMAIL=operator@enlightra.com

# Code
import api_auth
import api_abstraction

auth = api_auth.AuthService(user='operator@enlightra.com')
auth.__enter__()  # Handles OAuth2 automatically
mira = api_abstraction.combs.linear_measurements.CombsLinearMeasurements(auth)
order_info = mira.get_order_info(order_id=123)  # Just works!
```

**Benefits:**
✅ No manual OAuth2 configuration
✅ No credential management
✅ Automatic token refresh
✅ Retry logic built-in
✅ Less code to maintain

---

## API Endpoints (No Changes)

All API endpoints remain the same:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/orders/{order_id}` | Get single order |
| POST | `/api/v1/orders/bulk` | Get multiple orders (1-4) |
| GET | `/api/v1/orders/{id}/devices/{id}/picture` | Get device picture |
| GET | `/api/v1/orders/health` | Health check |

---

## Frontend (No Changes)

Frontend integration remains exactly the same. No changes needed.

---

## Testing

### Quick Test
```bash
# Terminal 1: Start backend
cd backend && fastapi dev app/main.py

# Terminal 2: Test endpoint
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis"

# Save token, then:
export TOKEN="<your-token>"
curl -X GET "http://localhost:8000/api/v1/orders/123" \
  -H "Authorization: Bearer $TOKEN"
```

### Full Stack Test
```bash
# Terminal 1: Backend
cd backend && fastapi dev app/main.py

# Terminal 2: Frontend
cd frontend && npm run dev

# Browser: http://localhost:5173
# 1. Login
# 2. Enter order ID
# 3. Click "Load Devices"
```

---

## Support

### Package Issues
- **api-auth issues**: Contact Timofey Shpakovsky (timofey.shpakovsky@gmail.com)
- **api-abstraction issues**: Contact Timofey Shpakovsky
- **MIRA API issues**: Contact MIRA admin

### zero-db Integration Issues
- **Email**: lucas.braud@enlightra.com
- **GitHub Issues**: https://github.com/your-org/zero-db/issues

---

## Summary

### What You Need to Know

1. **No manual OAuth2 setup** - handled by `api-auth` package
2. **GitLab access required** - for package installation
3. **Only 3 env vars needed**:
   - `MIRA_BASE_URL` (prod)
   - `MIRA_BASE_URL_DEV` (dev)
   - `MIRA_MEASURER_EMAIL` (your email)
4. **Everything else is automatic**

### Installation Time: ~5 minutes

1. Configure GitLab auth (1 min)
2. Run `uv sync` (2 min)
3. Update `.env` (1 min)
4. Start backend and test (1 min)

---

**Last Updated**: 2025-11-14
**Version**: 2.0.0 (Simplified with api-auth/api-abstraction)
**Author**: Lucas Braud
