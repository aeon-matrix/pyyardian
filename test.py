import aiohttp
import asyncio
from pyyardian.async_client import AsyncYardianClient

async def main():
    # Toggle between 192.168.1.103 (YP) and 192.168.1.104 (YC)
    host = "192.168.1.104" 
    token = "FCE25479" 

    async with aiohttp.ClientSession() as session:
        try:
            print(f"--- Connecting to {host} ---")
            cli = await AsyncYardianClient.create(session, host, token)
            print(f"SUCCESS! Model: {cli.model_type.upper()}")
            
            state = await cli.fetch_device_state()
            print(f"\nZones Total: {len(state.zones)}")
            print(f"Active IDs: {list(state.active_zones)}")
            for i, z in enumerate(state.zones):
                print(f"Zone {i+1}: {z[0]}")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())