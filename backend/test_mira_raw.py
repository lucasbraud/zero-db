#!/usr/bin/env python
"""
Raw test of api-abstraction directly.
"""
import os

# Set environment variables BEFORE ANY imports
os.environ['DBMS_ADDRESS'] = 'https://mira.enlightra.com'
os.environ['AUTH_SERVICE_CLIENT_SECRET'] = '14ruc7faalscdcdvgjr8cfveusk88gjaanks7ud50em7na0v3mn5'

import api_auth
import api_abstraction.combs.linear_measurements
import json

print('Testing api-abstraction directly...\n')

# Create auth service
auth = api_auth.AuthService()
auth.__enter__()

# Create MIRA client
mira = api_abstraction.combs.linear_measurements.CombsLinearMeasurements(auth_service=auth)

# Fetch order info
print(f'Calling get_order_info(order_id=280)...')
order_info = mira.get_order_info(order_id=280)

print(f'\nRaw response type: {type(order_info)}')
print(f'Raw response: {json.dumps(order_info, indent=2, default=str)[:1000]}...')

auth.__exit__(None, None, None)
