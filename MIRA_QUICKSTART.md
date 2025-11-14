# MIRA Integration Quick Start

Get up and running with MIRA database integration in 5 minutes.

---

## Prerequisites

1. **GitLab Access**: Access to `api-auth` and `api-abstraction` repositories (SSH or PAT)
2. **Backend**: Python 3.11+, uv package manager
3. **Frontend**: Node.js 20+, npm

**Note**: No manual MIRA OAuth2 credentials needed! Authentication is handled by Timofey's `api-auth` package.

---

## Step 1: Configure Environment (1 minute)

### Edit `.env` file
```bash
# Open .env in root directory
nano .env  # or your preferred editor
```

### Update MIRA settings
```bash
# Find these lines and update:
MIRA_MEASURER_EMAIL=your.email@enlightra.com  # Your email for tracking
```

**That's it!** No `MIRA_CLIENT_SECRET` or other OAuth2 credentials needed.

### Save and close
```bash
# Ctrl+X, then Y, then Enter (in nano)
```

---

## Step 2: Install Dependencies & Start Backend (2 minutes)

```bash
cd backend
uv sync  # Installs api-auth and api-abstraction from GitLab
source .venv/bin/activate  # Windows: .venv\Scripts\activate
fastapi dev app/main.py
```

**Note**: `uv sync` will install `api-auth` and `api-abstraction` from GitLab repositories. Make sure you have GitLab access configured (see [MIRA_SETUP_SIMPLIFIED.md](MIRA_SETUP_SIMPLIFIED.md) for GitLab authentication setup).

**Wait for:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Keep this terminal open!

---

## Step 3: Start Frontend (1 minute)

**New terminal:**
```bash
cd frontend
npm install  # First time only
npm run dev
```

**Wait for:**
```
  ➜  Local:   http://localhost:5173/
```

---

## Step 4: Test Integration (1 minute)

### Option A: Automated Test Script
```bash
# New terminal, from project root
./scripts/test_mira_integration.sh 123
```

Replace `123` with a real order ID from MIRA.

**Expected output:**
```
=== MIRA Integration Test ===
[1/6] Getting access token...
✓ Access token obtained

[2/6] Testing MIRA health check...
✓ MIRA is healthy

[3/6] Getting order 123...
✓ Order retrieved successfully
Order Name: Production Run 2024-01
Device Count: 24

... (more tests)

✓ All tests passed!
```

### Option B: Manual Test in Browser

1. **Open browser**: http://localhost:5173
2. **Login**:
   - Email: `admin@example.com`
   - Password: `changethis`
3. **Load order**:
   - Enter order ID: `123` (or your test order)
   - Click "Add"
   - Click "Load Devices"
4. **Verify**:
   - Devices appear in cards
   - Thumbnails load
   - Click thumbnail to see full image

---

## Step 5: Verify Everything Works

### ✅ Backend Checklist
- [ ] Backend running on http://localhost:8000
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Health check passes: `/api/v1/orders/health`
- [ ] No errors in terminal logs

### ✅ Frontend Checklist
- [ ] Frontend running on http://localhost:5173
- [ ] Login successful
- [ ] Order selector visible
- [ ] Can add/remove order IDs
- [ ] "Load Devices" button works
- [ ] Devices display with thumbnails

### ✅ MIRA Integration Checklist
- [ ] Orders load from MIRA (dev or prod)
- [ ] Device list displays correctly
- [ ] Device pictures load
- [ ] Measurement parameters shown
- [ ] No 401/403/404 errors in browser console

---

## Common Issues & Quick Fixes

### ❌ "Failed to install api-auth from GitLab"
**Fix:** Configure GitLab authentication (SSH key or Personal Access Token). See [MIRA_SETUP_SIMPLIFIED.md](MIRA_SETUP_SIMPLIFIED.md)

### ❌ "ImportError: No module named 'api_auth'"
**Fix:** Reinstall packages: `cd backend && uv sync`

### ❌ "Failed to fetch orders"
**Fix:** Ensure backend is running on port 8000

### ❌ Images not loading
**Fix:** Check browser console, verify order has devices with pictures

### ❌ "Order not found" (404)
**Fix:** Use valid order ID from MIRA environment (dev/prod)

---

## Next Steps

### 📚 Documentation
- **Full Integration Guide**: `MIRA_INTEGRATION.md`
- **API Endpoints**: http://localhost:8000/docs (when backend running)
- **Project README**: `README.md`

### 🚀 Development
1. **Create measurements**: Integrate with measurement control system
2. **Add filtering**: Search devices by name/geometry
3. **Export data**: CSV export for device lists
4. **Measurement queue**: Add devices to measurement queue

### 🧪 Testing
```bash
# Backend tests
cd backend
bash ./scripts/test.sh

# Frontend E2E tests
cd frontend
npx playwright test
```

---

## Quick Reference

### Environment Variables
```bash
ENVIRONMENT=local                                    # local, staging, production
MIRA_BASE_URL_DEV=https://dev.mira.enlightra.com   # Development URL
MIRA_BASE_URL=https://mira.enlightra.com           # Production URL
MIRA_MEASURER_EMAIL=operator@enlightra.com         # Your email

# Note: OAuth2 credentials (CLIENT_ID, CLIENT_SECRET) are handled by api-auth package
```

### URLs
| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MIRA Dev | https://dev.mira.enlightra.com |
| MIRA Prod | https://mira.enlightra.com |

### Default Credentials
| User | Email | Password |
|------|-------|----------|
| Admin | admin@example.com | changethis |

⚠️ **Change these in production!**

---

## Getting Help

### 1. Check Logs
```bash
# Backend logs (terminal where fastapi is running)
# Look for errors starting with "ERROR:" or "WARNING:"

# Frontend logs (browser)
# Open DevTools (F12) → Console tab
```

### 2. Check Troubleshooting Guide
See `MIRA_INTEGRATION.md` → "Troubleshooting" section

### 3. Test Individual Components
```bash
# Test MIRA health
curl -X GET "http://localhost:8000/api/v1/orders/health" \
  -H "Authorization: Bearer <your-token>"

# Test order retrieval
curl -X GET "http://localhost:8000/api/v1/orders/123" \
  -H "Authorization: Bearer <your-token>"
```

### 4. Contact Support
- **Email**: lucas.braud@enlightra.com
- **GitHub Issues**: https://github.com/your-org/zero-db/issues

---

**Total Setup Time**: ~5 minutes
**Last Updated**: 2025-11-14
