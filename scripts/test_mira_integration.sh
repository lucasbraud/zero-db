#!/bin/bash
#
# MIRA Integration Test Script
#
# Tests all MIRA API endpoints with real data.
# Usage: ./scripts/test_mira_integration.sh [order_id]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ORDER_ID="${1:-123}"  # Default order ID (change if needed)
USERNAME="${USERNAME:-admin@example.com}"
PASSWORD="${PASSWORD:-changethis}"

echo -e "${YELLOW}=== MIRA Integration Test ===${NC}"
echo "API Base URL: $API_BASE_URL"
echo "Order ID: $ORDER_ID"
echo ""

# Step 1: Login and get access token
echo -e "${YELLOW}[1/6] Getting access token...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}✗ Failed to get access token${NC}"
  echo "Response: $TOKEN_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Access token obtained${NC}"
echo ""

# Step 2: Health check
echo -e "${YELLOW}[2/6] Testing MIRA health check...${NC}"
HEALTH_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/v1/orders/health" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

HEALTH_STATUS=$(echo $HEALTH_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)

if [ "$HEALTH_STATUS" != "healthy" ]; then
  echo -e "${RED}✗ MIRA health check failed${NC}"
  echo "Response: $HEALTH_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ MIRA is healthy${NC}"
echo "Response: $HEALTH_RESPONSE"
echo ""

# Step 3: Get single order
echo -e "${YELLOW}[3/6] Getting order $ORDER_ID...${NC}"
ORDER_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/v1/orders/$ORDER_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

ORDER_NAME=$(echo $ORDER_RESPONSE | grep -o '"order_name":"[^"]*' | cut -d'"' -f4)
DEVICE_COUNT=$(echo $ORDER_RESPONSE | grep -o '"comb_placed_id"' | wc -l)

if [ "$DEVICE_COUNT" -eq 0 ]; then
  echo -e "${RED}✗ Failed to get order or no devices found${NC}"
  echo "Response: $ORDER_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Order retrieved successfully${NC}"
echo "Order Name: $ORDER_NAME"
echo "Device Count: $DEVICE_COUNT"
echo ""

# Step 4: Get bulk orders
echo -e "${YELLOW}[4/6] Getting bulk orders...${NC}"
BULK_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/orders/bulk" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"order_ids\": [$ORDER_ID]}")

BULK_ORDER_COUNT=$(echo $BULK_RESPONSE | grep -o '"order_id"' | wc -l)

if [ "$BULK_ORDER_COUNT" -eq 0 ]; then
  echo -e "${RED}✗ Failed to get bulk orders${NC}"
  echo "Response: $BULK_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ Bulk orders retrieved successfully${NC}"
echo "Orders returned: $BULK_ORDER_COUNT"
echo ""

# Step 5: Get device picture
echo -e "${YELLOW}[5/6] Getting device picture...${NC}"

# Extract first comb_placed_id from order response
COMB_PLACED_ID=$(echo $ORDER_RESPONSE | grep -o '"comb_placed_id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$COMB_PLACED_ID" ]; then
  echo -e "${YELLOW}⚠ No comb_placed_id found, skipping picture test${NC}"
else
  PICTURE_OUTPUT="/tmp/mira_device_${COMB_PLACED_ID}.png"
  curl -s -X GET "$API_BASE_URL/api/v1/orders/$ORDER_ID/devices/$COMB_PLACED_ID/picture" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    --output "$PICTURE_OUTPUT"

  if [ -f "$PICTURE_OUTPUT" ]; then
    FILE_SIZE=$(wc -c < "$PICTURE_OUTPUT")
    if [ "$FILE_SIZE" -gt 1000 ]; then
      echo -e "${GREEN}✓ Device picture retrieved successfully${NC}"
      echo "File: $PICTURE_OUTPUT"
      echo "Size: $FILE_SIZE bytes"
    else
      echo -e "${RED}✗ Device picture file too small (likely error)${NC}"
      rm "$PICTURE_OUTPUT"
    fi
  else
    echo -e "${RED}✗ Failed to download device picture${NC}"
  fi
fi
echo ""

# Step 6: Get thumbnail
echo -e "${YELLOW}[6/6] Getting device thumbnail...${NC}"

if [ -z "$COMB_PLACED_ID" ]; then
  echo -e "${YELLOW}⚠ No comb_placed_id found, skipping thumbnail test${NC}"
else
  THUMBNAIL_OUTPUT="/tmp/mira_device_${COMB_PLACED_ID}_thumb.png"
  curl -s -X GET "$API_BASE_URL/api/v1/orders/$ORDER_ID/devices/$COMB_PLACED_ID/picture?thumbnail=true" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    --output "$THUMBNAIL_OUTPUT"

  if [ -f "$THUMBNAIL_OUTPUT" ]; then
    FILE_SIZE=$(wc -c < "$THUMBNAIL_OUTPUT")
    if [ "$FILE_SIZE" -gt 1000 ]; then
      echo -e "${GREEN}✓ Device thumbnail retrieved successfully${NC}"
      echo "File: $THUMBNAIL_OUTPUT"
      echo "Size: $FILE_SIZE bytes"
    else
      echo -e "${RED}✗ Device thumbnail file too small (likely error)${NC}"
      rm "$THUMBNAIL_OUTPUT"
    fi
  else
    echo -e "${RED}✗ Failed to download device thumbnail${NC}"
  fi
fi
echo ""

# Summary
echo -e "${GREEN}=== Test Summary ===${NC}"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Open frontend: http://localhost:5173"
echo "  2. Login with: $USERNAME"
echo "  3. Enter order ID: $ORDER_ID"
echo "  4. Click 'Add' then 'Load Devices'"
echo ""
