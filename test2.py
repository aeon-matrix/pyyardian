import aiohttp
import asyncio
import json

async def main():
    host = "192.168.1.103"
    port = 880
    token = "FCE25479"
    
    # We use the root URL because your successful curl used the root
    url = f"http://{host}:{port}"
    
    # Matching your successful Git Bash headers exactly
    headers = {
        "Yardian-Token": token,
        "Content-Type": "application/json"
    }
    
    # Matching your successful stringified payload
    payload = {
        "sEvent": "AE_IRR_START_INST",
        "sPayload": "[[-1, 0, 0, 0, 60]]"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            result = await response.json()
            print(f"Status Code: {response.status}")
            print(f"Response Body: {result}")

if __name__ == "__main__":
    asyncio.run(main())
    