# ⚠️ IMPORTANT: MIRA Secret Required

## Issue

The MIRA integration requires the **OAuth2 client secret** to authenticate with the MIRA API.

## What You Need

You need to set the `AUTH_SERVICE_CLIENT_SECRET` environment variable in the `.env` file.

### Where to Get the Secret

**Contact one of the following:**
1. **Timofey Shpakovsky** (timofey.shpakovsky@gmail.com) - Author of api-auth package
2. **MIRA Administrator** - Your organization's MIRA admin
3. **DevOps Team** - May have secrets in vault

### How to Set It

1. Open `.env` file in the project root:
   ```bash
   nano .env
   ```

2. Find this line:
   ```bash
   AUTH_SERVICE_CLIENT_SECRET=changethis
   ```

3. Replace `changethis` with the actual secret:
   ```bash
   AUTH_SERVICE_CLIENT_SECRET=<your-actual-secret-here>
   ```

4. Save and restart the backend

## Testing

Once you have the secret set, test it:

```bash
cd backend
source .venv/bin/activate

# Test dev environment
python -c "
import asyncio
from app.services.mira_client_v2 import MIRAClient

async def test():
    mira = MIRAClient(base_url='https://dev.mira.enlightra.com')
    result = await mira.get_order_info(272)
    if result.is_ok():
        print('✅ Successfully connected to MIRA!')
        order = result.unwrap()
        print(f'Order: {order.get(\"order_name\")}')
        print(f'Devices: {len(order.get(\"devices\", []))}')
    else:
        print(f'❌ Error: {result.error}')
    await mira.close()

asyncio.run(test())
"
```

## Current Status

❌ **MIRA integration is NOT functional** until you set the secret.

## Why This Wasn't Mentioned Before

The `api-auth` package reads OAuth2 credentials from environment variables (not from code). While we eliminated the need to manage tokens manually, we still need the **initial secret** that the package uses to obtain tokens.

This is similar to how it works in `measurement-control-logic` - you still need the secret set in your environment.

## What Changes

### Before (Our initial plan)
- ❌ We thought: "No secrets needed, api-auth handles everything"
- ✅ Reality: "api-auth handles token management, but needs the initial secret"

### Now (Correct understanding)
- ✅ **Secret needed**: `AUTH_SERVICE_CLIENT_SECRET` in `.env`
- ✅ **Token management**: Automatic (handled by api-auth)
- ✅ **Token refresh**: Automatic (handled by api-auth)

## Summary

**You need ONE secret:**
- `AUTH_SERVICE_CLIENT_SECRET` - Get from MIRA admin or Timofey

**Everything else is automatic:**
- Token acquisition ✅
- Token refresh ✅
- Retry on 401 ✅

---

**Contact**: lucas.braud@enlightra.com if you need help getting the secret.
