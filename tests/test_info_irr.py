import aiohttp
import asyncio
from pyyardian.async_client import AsyncYardianClient

async def main():
    host = "192.168.1.104" 
    token = "FCE25479" 

    async with aiohttp.ClientSession() as session:
        try:
            cli = await AsyncYardianClient.create(session, host, token)
            info = await cli.fetch_device_info()
            
            print(f"--- Device Info for {info.get('model')} ---")
            print(f"Serial: {info.get('serialNumber')}")
            print(f"Firmware (yid): {info.get('yid')}")
            
            # Check if constants were merged correctly
            if "description" in info:
                print(f"Model Description: {info['description']}")
            
            # Verify we can see the zone metadata
            state = await cli.fetch_device_state()
            for i, zone in enumerate(state.zones):
                # YP format: [name, enabled, mv_link, unstable]
                print(f"Zone {i+1} Name: {zone[0]}")

        except Exception as e:
            print(f"INFO TEST FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())