# MIRA Database Integration Guide

## Overview

This document provides comprehensive guidance for the MIRA database integration in zero-db. The integration allows users to retrieve order information, device lists, and device pictures from the MIRA database for measurement preparation.

---

## Architecture

### Backend Stack
- **Framework**: FastAPI (async-first)
- **Authentication**: AWS Cognito OAuth2 (client credentials flow)
- **HTTP Client**: httpx.AsyncClient (connection pooling)
- **Caching**: File-based cache in `/tmp/mira_cache` (TTL: 30 minutes)
- **Image Processing**: PIL/Pillow for thumbnail generation

### Frontend Stack
- **Framework**: React + TypeScript
- **UI Library**: Chakra UI
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: TanStack Router
- **State Management**: React hooks (useState)

### Data Flow
```
User → Frontend Dashboard
  ↓
React Query (useOrdersBulk)
  ↓
Backend API (/api/v1/orders/bulk)
  ↓
MIRA Client (OAuth2 + caching)
  ↓
MIRA Database API (dev/prod)
```

---

## Configuration

### Environment Variables

#### `.env` (root directory)
```bash
# MIRA Database Configuration
MIRA_BASE_URL=https://mira.enlightra.com              # Production URL
MIRA_BASE_URL_DEV=https://dev.mira.enlightra.com     # Development URL
MIRA_CLIENT_ID=56a17up5ouquq9jfep9nbh2a0u
MIRA_CLIENT_SECRET=<your-secret-here>                 # CHANGE THIS!
MIRA_TOKEN_URL=https://eu-central-1meowq2nyq.auth.eu-central-1.amazoncognito.com/oauth2/token
MIRA_SCOPE=default-m2m-resource-server-btncxn
MIRA_CACHE_TTL_SECONDS=1800                           # 30 minutes
MIRA_MAX_ORDERS_PER_REQUEST=4
MIRA_MEASURER_EMAIL=operator@enlightra.com
```

#### Environment-Based URL Selection
- `ENVIRONMENT=production` → uses `MIRA_BASE_URL` (prod)
- `ENVIRONMENT=staging` → uses `MIRA_BASE_URL_DEV` (dev)
- `ENVIRONMENT=local` → uses `MIRA_BASE_URL_DEV` (dev)

### Security Notes
1. **NEVER commit** `MIRA_CLIENT_SECRET` to version control
2. Use different secrets for dev/staging/production
3. Rotate secrets quarterly
4. Store production secrets in secure vault (e.g., AWS Secrets Manager)

---

## API Endpoints

### Backend Routes

All routes require authentication (JWT token from `/api/v1/login/access-token`).

#### 1. Get Single Order
```http
GET /api/v1/orders/{order_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "order_id": 123,
  "order_name": "Production Run 2024-01",
  "devices": [
    {
      "comb_placed_id": 456,
      "waveguide_name": "WG_001",
      "devices_set_connector_id": 789,
      "input_port_position": {
        "position_x_um": 1000.0,
        "position_y_um": 2000.0,
        "position_z_um": null
      },
      "output_port_position": {
        "position_x_um": 1100.0,
        "position_y_um": 2100.0,
        "position_z_um": null
      },
      "geometry": {
        "gap_um": 0.5,
        "bus_width_um": 1.2,
        "coupling_length_um": 50.0,
        "ring_radius_um": 100.0
      },
      "picture_url": "/api/v1/orders/123/devices/456/picture"
    }
  ],
  "measurement_parameters": {
    "laser_power_db": 0.0,
    "sweep_speed": 100,
    "start_wl_nm": 1530.0,
    "stop_wl_nm": 1565.0,
    "resolution_nm": 0.01
  },
  "calibrated_setup_id": null
}
```

#### 2. Get Multiple Orders (Bulk)
```http
POST /api/v1/orders/bulk
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_ids": [123, 124, 125]
}
```

**Response:** Array of OrderInfoResponse (same structure as single order)

**Validation:**
- Minimum 1 order ID
- Maximum 4 order IDs (configurable via `MIRA_MAX_ORDERS_PER_REQUEST`)

#### 3. Get Device Picture
```http
GET /api/v1/orders/{order_id}/devices/{comb_placed_id}/picture?thumbnail=false
Authorization: Bearer <token>
```

**Query Parameters:**
- `thumbnail` (optional, boolean): If `true`, returns 256x256 thumbnail

**Response:**
- Content-Type: `image/png`
- Cache-Control: `public, max-age=1800`
- Body: PNG image bytes

#### 4. MIRA Health Check
```http
GET /api/v1/orders/health
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "healthy",
  "mira_base_url": "https://dev.mira.enlightra.com",
  "environment": "local"
}
```

---

## Frontend Components

### 1. Dashboard (`/frontend/src/routes/_layout/index.tsx`)
Main page integrating all MIRA components.

**Features:**
- Welcome message with user name
- Order selector
- Device list with tabs
- Loading/error states

### 2. OrderSelector (`/frontend/src/components/Orders/OrderSelector.tsx`)
Allows users to input and manage 1-4 order IDs.

**Features:**
- Number input with validation
- Add/remove order IDs
- Tag display for selected orders
- Load button with loading state
- Input validation (positive integers, no duplicates, max 4)

### 3. DeviceList (`/frontend/src/components/Orders/DeviceList.tsx`)
Displays devices grouped by order using tabs (if multiple orders).

**Features:**
- Single order: direct grid view
- Multiple orders: tabbed interface
- Measurement parameters display
- Device count badges

### 4. DeviceCard (`/frontend/src/components/Orders/DeviceCard.tsx`)
Individual device card with thumbnail and details.

**Features:**
- Device picture thumbnail (256x256)
- Click to view full-size image (modal)
- Device information: waveguide name, positions, geometry
- "Select for Measurement" button
- Loading skeleton for images

### 5. Custom Hook: useOrders (`/frontend/src/hooks/useOrders.ts`)
TanStack Query hooks for fetching orders.

**Functions:**
- `useOrder(orderId, token)`: Fetch single order
- `useOrdersBulk(orderIds, token)`: Fetch multiple orders
- `getDevicePictureUrl(orderId, combPlacedId, thumbnail)`: Generate picture URL

**Caching:**
- Stale time: 30 minutes
- Garbage collection time: 1 hour
- Query keys: `['orders', orderId]` or `['orders', 'bulk', sortedOrderIds]`

---

## Testing Guide

### Backend Testing

#### 1. Start Backend
```bash
cd backend
uv sync
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Set MIRA credentials in .env first!
fastapi dev app/main.py
```

Backend will be available at: http://localhost:8000

#### 2. Get Access Token
```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changethis"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save the `access_token` for subsequent requests.

#### 3. Test MIRA Health Check
```bash
export TOKEN="<your-access-token>"

curl -X GET "http://localhost:8000/api/v1/orders/health" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "mira_base_url": "https://dev.mira.enlightra.com",
  "environment": "local"
}
```

#### 4. Test Get Single Order
```bash
# Replace 123 with a real order_id from MIRA dev
curl -X GET "http://localhost:8000/api/v1/orders/123" \
  -H "Authorization: Bearer $TOKEN"
```

**Success:** Returns OrderInfoResponse with devices
**Failure (404):** Order not found or MIRA API error

#### 5. Test Get Multiple Orders
```bash
curl -X POST "http://localhost:8000/api/v1/orders/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_ids": [123, 124]}'
```

#### 6. Test Get Device Picture
```bash
# Replace 123 and 456 with real order_id and comb_placed_id
curl -X GET "http://localhost:8000/api/v1/orders/123/devices/456/picture" \
  -H "Authorization: Bearer $TOKEN" \
  --output device_picture.png
```

Open `device_picture.png` to verify image.

#### 7. Test Thumbnail Generation
```bash
curl -X GET "http://localhost:8000/api/v1/orders/123/devices/456/picture?thumbnail=true" \
  -H "Authorization: Bearer $TOKEN" \
  --output device_thumbnail.png
```

Thumbnail should be 256x256 pixels.

### Frontend Testing

#### 1. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

#### 2. Login
1. Navigate to http://localhost:5173
2. Click "Log In"
3. Enter credentials: `admin@example.com` / `changethis`
4. Click "Log In"

#### 3. Test Order Selection
1. On the dashboard, enter an order ID (e.g., 123)
2. Click "Add"
3. Verify order tag appears
4. Add 2-3 more order IDs (max 4)
5. Try adding a 5th order → should show warning toast
6. Try adding duplicate order → should show warning toast
7. Click "X" on a tag to remove an order

#### 4. Test Load Devices
1. Click "Load Devices" button
2. Verify loading spinner appears
3. Wait for devices to load
4. Verify:
   - For 1 order: direct grid view
   - For 2+ orders: tabbed interface with order tabs
   - Device cards show thumbnails, names, positions

#### 5. Test Device Pictures
1. Verify thumbnails load in device cards
2. Click on a thumbnail
3. Verify full-size image opens in modal
4. Close modal
5. Repeat for multiple devices

#### 6. Test Error Handling
1. Enter an invalid order ID (e.g., 999999)
2. Click "Load Devices"
3. Verify error alert appears with error message
4. Remove invalid order and add valid one
5. Verify devices load correctly

#### 7. Test Caching
1. Load an order
2. Clear selection
3. Re-add the same order and load
4. Verify data loads faster (from cache)
5. Check browser DevTools Network tab → should see cached response

### Integration Testing (Full Stack)

#### 1. Start Full Stack
```bash
# Terminal 1: Backend
cd backend
fastapi dev app/main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

#### 2. End-to-End Flow
1. Login to frontend
2. Select order IDs: 123, 124
3. Click "Load Devices"
4. Verify both orders load with devices
5. Switch between tabs
6. Click "Select for Measurement" on a device
7. Verify success toast appears

#### 3. Performance Testing
1. Select 4 orders with many devices each
2. Click "Load Devices"
3. Measure load time:
   - First load (cold cache): ~2-5 seconds
   - Subsequent load (warm cache): <500ms
4. Scroll through device cards
5. Verify images load progressively

#### 4. Multi-User Testing
1. Open 2 browser windows
2. Login with different users
3. Load same order in both windows
4. Verify cache is shared (backend cache)
5. Verify both users see same data

---

## Troubleshooting

### Backend Issues

#### 1. "MIRA integration is not configured"
**Cause:** `MIRA_CLIENT_ID` or `MIRA_CLIENT_SECRET` not set

**Solution:**
```bash
# Check .env file
cat .env | grep MIRA_CLIENT

# Set values
echo "MIRA_CLIENT_ID=56a17up5ouquq9jfep9nbh2a0u" >> .env
echo "MIRA_CLIENT_SECRET=<your-secret>" >> .env
```

#### 2. "Failed to get access token: HTTP 401"
**Cause:** Invalid OAuth2 credentials

**Solution:**
1. Verify `MIRA_CLIENT_ID` and `MIRA_CLIENT_SECRET` are correct
2. Check if credentials are for correct environment (dev/prod)
3. Contact MIRA admin to verify credentials

#### 3. "Failed to get order information: HTTP 404"
**Cause:** Order ID doesn't exist in MIRA

**Solution:**
1. Verify order ID is correct
2. Check if using correct environment (dev orders != prod orders)
3. Try known order IDs from MIRA UI

#### 4. "Failed to get device picture: GZIP decompression error"
**Cause:** Image data is not GZIP-compressed or corrupted

**Solution:**
1. Check MIRA API response format
2. Verify `comb_placed_id` is valid
3. Try different device

#### 5. Cache Issues
**Problem:** Stale data being served

**Solution:**
```bash
# Clear backend cache
rm -rf /tmp/mira_cache/*

# Or restart backend
# Cache will auto-refresh after TTL (30 minutes)
```

### Frontend Issues

#### 1. "Failed to fetch orders"
**Cause:** Backend not running or CORS issue

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/docs

# Check CORS settings in backend/.env
# BACKEND_CORS_ORIGINS should include frontend URL
```

#### 2. Images Not Loading
**Cause:** Invalid picture URL or authentication issue

**Solution:**
1. Check browser DevTools Console for errors
2. Verify access token is valid (not expired)
3. Check Network tab for 401/403 errors
4. Try manual picture URL: http://localhost:8000/api/v1/orders/123/devices/456/picture

#### 3. "Cannot read property 'devices' of undefined"
**Cause:** Order response doesn't match expected schema

**Solution:**
1. Check backend response in Network tab
2. Verify MIRA API response structure
3. Update TypeScript types if MIRA schema changed

#### 4. React Query Errors
**Problem:** "Query is already fetching"

**Solution:**
```typescript
// Add refetchOnWindowFocus: false
useQuery({
  queryKey: ['orders', orderId],
  queryFn: () => fetchOrder(orderId, token),
  refetchOnWindowFocus: false,
})
```

---

## Performance Optimization

### Backend
1. **Caching**: 30-minute TTL reduces MIRA API calls by ~95%
2. **Connection Pooling**: httpx.AsyncClient reuses connections
3. **Parallel Fetching**: `asyncio.gather()` for bulk requests
4. **Lazy Token Refresh**: Only refresh when needed (5min buffer)

### Frontend
1. **React Query Caching**: 30-minute stale time, 1-hour GC time
2. **Image Lazy Loading**: Thumbnails only load when visible
3. **Code Splitting**: Components loaded on-demand
4. **Optimistic Updates**: Instant UI feedback

### Recommended Load Limits
- **Max orders per request**: 4 (configurable)
- **Max devices per order**: 1000 (MIRA limit)
- **Max thumbnail size**: 256x256 pixels
- **Image cache size**: ~50MB for 100 devices

---

## Future Enhancements

### Phase 2 (Q2 2024)
- [ ] Device selection persistence (localStorage)
- [ ] Export device list to CSV
- [ ] Search/filter devices by name or geometry
- [ ] Bulk device selection (checkbox)
- [ ] Measurement queue management

### Phase 3 (Q3 2024)
- [ ] Real-time order updates (WebSocket)
- [ ] Offline mode with IndexedDB cache
- [ ] Advanced image viewer (zoom, pan, annotations)
- [ ] Device comparison view (side-by-side)
- [ ] Measurement history per device

### Phase 4 (Q4 2024)
- [ ] Mobile-responsive design
- [ ] PWA support
- [ ] Dark mode
- [ ] Accessibility improvements (WCAG 2.1 AA)

---

## API Reference

### MIRAClient Methods

#### `get_order_info(order_id: int) -> Result[dict, str]`
Get order information including devices and measurement parameters.

**Parameters:**
- `order_id`: Order ID from MIRA

**Returns:**
- `Ok(dict)`: Order info dict
- `Err(str)`: Error message

**Caching:** Yes (30 minutes)

#### `get_device_picture(comb_placed_id: int) -> Result[bytes, str]`
Get device picture (PNG, decompressed).

**Parameters:**
- `comb_placed_id`: Comb placed ID

**Returns:**
- `Ok(bytes)`: PNG image bytes
- `Err(str)`: Error message

**Caching:** Yes (30 minutes)

#### `get_setups() -> Result[list[dict], str]`
Get available measurement setups.

**Returns:**
- `Ok(list[dict])`: List of setup dicts
- `Err(str)`: Error message

**Caching:** Yes (30 minutes)

#### `create_measurement(...) -> Result[int, str]`
Create measurement entry in MIRA.

**Parameters:**
- `devices_set_connector_id`: Device set connector ID
- `setup_id`: Setup ID
- `software_id`: Software ID
- `probe_station_mode_id`: Probe station mode ID
- `measurer_email`: Measurer email (optional)

**Returns:**
- `Ok(int)`: Measurement ID
- `Err(str)`: Error message

**Caching:** No

#### `upload_measurement_data(measurement_id: int, csv_content: str) -> Result[bool, str]`
Upload measurement CSV data.

**Parameters:**
- `measurement_id`: Measurement ID
- `csv_content`: CSV file content as string

**Returns:**
- `Ok(bool)`: Success
- `Err(str)`: Error message

**Caching:** No

#### `health_check() -> Result[bool, str]`
Check MIRA API connectivity.

**Returns:**
- `Ok(bool)`: Healthy
- `Err(str)`: Error message

**Caching:** No

---

## Security Best Practices

### Backend
1. **Secrets Management**
   - Store `MIRA_CLIENT_SECRET` in environment variables
   - Use different secrets per environment
   - Never log secrets
   - Rotate quarterly

2. **Authentication**
   - JWT tokens for user authentication
   - OAuth2 for MIRA API authentication
   - Token expiry: 8 days (user), 1 hour (MIRA)
   - Automatic token refresh

3. **Authorization**
   - All order endpoints require authentication
   - No role-based restrictions (all authenticated users can access any order)
   - Audit logging (TODO: Phase 2)

4. **Data Validation**
   - Pydantic models validate all I/O
   - Order ID: positive integer
   - Max 4 orders per bulk request
   - Image size validation (TODO)

### Frontend
1. **Token Storage**
   - Access token in localStorage
   - Automatic removal on logout
   - Refresh token not exposed to JavaScript

2. **XSS Prevention**
   - React escapes all user input by default
   - No `dangerouslySetInnerHTML` usage

3. **CORS**
   - Backend whitelist: localhost:5173 (dev)
   - Production: specific frontend domain only

---

## Monitoring & Logging

### Backend Logs
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Log Locations:**
- Console output (development)
- `/var/log/fastapi/app.log` (production)
- Sentry (errors only)

**Key Log Messages:**
- `MIRA client initialized for {base_url}`
- `Successfully obtained MIRA access token`
- `User {email} requesting order {order_id}`
- `Cache hit for order {order_id}`
- `Failed to get order {order_id}: {error}`

### Frontend Logs
**React Query DevTools:**
```bash
# Already enabled in development
# Open browser DevTools → React Query tab
```

**Network Monitoring:**
```bash
# Browser DevTools → Network tab
# Filter: XHR
# Look for /api/v1/orders/* requests
```

---

## Support & Contact

### Documentation
- **FastAPI Docs**: http://localhost:8000/docs (when backend running)
- **MIRA API Docs**: https://dev.mira.enlightra.com/docs
- **Project README**: `/README.md`

### Team Contacts
- **Backend Lead**: lucas.braud@enlightra.com
- **MIRA Admin**: [MIRA admin contact]
- **DevOps**: [DevOps contact]

### Issue Reporting
1. Check troubleshooting section above
2. Search existing GitHub issues
3. Create new issue with:
   - Environment (dev/prod)
   - Steps to reproduce
   - Error messages (backend logs + browser console)
   - Screenshots (if applicable)

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
**Author**: Lucas Braud (lucas.braud@enlightra.com)
