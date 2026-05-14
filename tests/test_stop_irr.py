import aiohttp
import asyncio
from pyyardian.async_client import AsyncYardianClient

async def main():
    host = "192.168.1.104" # Change to .103 for YP
    token = "FCE25479" 

    async with aiohttp.ClientSession() as session:
        try:
            cli = await AsyncYardianClient.create(session, host, token)
            print(f"--- Testing STOP on {cli.model_type.upper()} ---")
            
            # 1. Start it first so we have something to stop
            await cli.start_irrigation(0, 120)
            print("Irrigation started...")
            await asyncio.sleep(5)

            # 2. Stop it
            print("Sending STOP command...")
            await cli.stop_irrigation()
            
            # 3. Verify
            await asyncio.sleep(2)
            active = await cli.fetch_active_zones()
            if not active:
                print("SUCCESS: All zones stopped.")
            else:
                print(f"FAILED: Zones still running: {active}")

        except Exception as e:
            print(f"STOP TEST FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
