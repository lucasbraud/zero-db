#!/usr/bin/env python
"""
Direct test of MIRA client with correct environment setup.
Sets DBMS_ADDRESS BEFORE any imports.
"""
import os
import asyncio

# Set environment variables BEFORE ANY imports
os.environ['DBMS_ADDRESS'] = 'https://mira.enlightra.com'
os.environ['AUTH_SERVICE_CLIENT_SECRET'] = '14ruc7faalscdcdvgjr8cfveusk88gjaanks7ud50em7na0v3mn5'

# Now import after environment is set
from app.services.mira_client_v2 import MIRAClient


async def main():
    print('✅ Testing production MIRA (order 280) with env set before imports...\n')

    mira = MIRAClient(base_url='https://mira.enlightra.com')
    result = await mira.get_order_info(280)

    if result.is_ok():
        order = result.unwrap()
        print(f'Order ID: {order.get("order_id")}')
        print(f'Order Name: {order.get("order_name")}')
        print(f'Number of devices: {len(order.get("devices", []))}')

        devices = order.get('devices', [])
        if devices:
            print('\nFirst 5 devices:')
            for i, device in enumerate(devices[:5]):
                print(f'  {i}: {device.get("waveguide_name")} (ID: {device.get("comb_placed_id")})')

        params = order.get('measurement_parameters', {})
        if params:
            print('\nMeasurement Parameters:')
            print(f'  Wavelength: {params.get("start_wl_nm")}-{params.get("stop_wl_nm")} nm')
            print(f'  Power: {params.get("laser_power_db")} dB')
            print(f'  Speed: {params.get("sweep_speed")} nm/s')
            print(f'  Temperature: {params.get("temperature_c")} °C')
            print(f'  Resolution: {params.get("resolution_nm")} nm')

        print('\n✅ Success! MIRA integration working correctly.')
    else:
        print(f'❌ Error: {result.error}')

    await mira.close()


if __name__ == '__main__':
    asyncio.run(main())
