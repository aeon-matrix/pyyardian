import aiohttp
import asyncio
from pyyardian.async_client import AsyncYardianClient

async def main():
    host = "192.168.1.104"
    token = "FCE25479" 
    
    async with aiohttp.ClientSession() as session:
        try:
            cli = await AsyncYardianClient.create(session, host, token)
            print(f"Starting irrigation on {cli.model_type.upper()}...")
            await cli.start_irrigation(zone_id=0, duration=60)
            print("Command Sent.")
            
            await asyncio.sleep(2)
            active = await cli.fetch_active_zones()
            print(f"Active Zones: {active}")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())