import aiohttp
import asyncio
from dataclasses import dataclass

from .const import MODEL_DETAIL, DEFAULT_TIMEOUT
from .exceptions import NotAuthorizedException, NetworkException
from .typing import DeviceInfo, OperationInfo

@dataclass
class YardianDeviceState:
    """Data retrieved from a Yardian device."""
    zones: list[list]
    active_zones: set[int]

class AsyncYardianClient:
    def __init__(
        self, websession: aiohttp.ClientSession, host: str, 
        token: str = None, username: str = "admin", password: str = "1234"
    ) -> None:
        """Initialize the client. Use .create() for async auto-detection."""
        self._websession = websession
        self._host = host
        self._token = token        # Static token for YP
        self._username = username  # YC default: admin
        self._password = password  # YC default: 1234
        self._base_url = f"http://{host}:880"
        self._base_header = {}        
        self._device_info = None
        self.model_type = "yp"

    @classmethod
    async def create(cls, websession: aiohttp.ClientSession, host: str, token: str = None, username: str = "admin", password: str = "1234"):
        """Asynchronous factory to create a client and auto-detect the model."""
        client = cls(websession, host, token, username, password)
        await client.detect_model()
        return client

    async def detect_model(self):
        """Identify YP or YC by testing Port 880 auth behavior."""
        url = f"http://{self._host}:880/API_GET_DEVICEINFO"
        try:
            async with self._websession.get(url, timeout=DEFAULT_TIMEOUT) as resp:
                data = await resp.json(content_type=None)
                
                # Behavioral Detection: YP returns -1000 without token
                if data.get("iCode") == -1000:
                    self.model_type = "yp"
                    self._base_url = f"http://{self._host}:880"
                    self._base_header = {"Yardian-Token": self._token}
                else:
                    # YC allows discovery without token
                    self.model_type = "yc"
                    self._base_url = f"http://{self._host}:80"
                    await self.login_yc() 
        except Exception as e:
            raise NetworkException(str(e))

    async def login_yc(self):
        """Exchange YC credentials for a JWT."""
        url = f"http://{self._host}:80/auth/login"
        payload = {"user_id": self._username, "password": self._password}
        async with self._websession.post(url, json=payload, timeout=DEFAULT_TIMEOUT) as resp:
            if resp.status == 200:
                # Handle text/plain JSON
                result = await resp.json(content_type=None)
                self._token = result["token"]
                self._base_header = {"Authorization": f"Bearer {self._token}"}
            else:
                raise NotAuthorizedException(f"YC Login Failed: {resp.status}")

    async def fetch_device_info(self) -> DeviceInfo:
        """Fetch model info on Port 880."""
        url = f"http://{self._host}:880/API_GET_DEVICEINFO"
        try:
            async with self._websession.get(url, headers=self._base_header, timeout=DEFAULT_TIMEOUT) as response:
                resp = await response.json(content_type=None)
                # Handle flat vs nested JSON
                result = resp.get("result", resp)
                model = result.get("model")
                return result | MODEL_DETAIL.get(model, {})
        except Exception:
            raise NetworkException()

    async def fetch_oper_info(self) -> OperationInfo:
        """Route to correct info endpoint."""
        endpoint = "/res/controller" if self.model_type == "yc" else "/API_MGR_GET_OPERINFO"
        async with self._websession.get(f"{self._base_url}{endpoint}", headers=self._base_header) as response:
            resp = await response.json(content_type=None)
            return resp.get("result", resp)

    async def fetch_active_zones(self):
        """Fetch currently running zone IDs."""
        endpoint = "/res/running-task" if self.model_type == "yc" else "/API_ZONE_GET_OPENINGZONE"
        async with self._websession.get(f"{self._base_url}{endpoint}", headers=self._base_header) as response:
            resp = await response.json(content_type=None)
            if self.model_type == "yc":
                return [task["output_id"] for task in resp]
            return resp.get("result", [])

    async def fetch_zone_info(self, amount=None):
        """Fetch zone metadata (names and status)."""
        if self.model_type == "yc":
            async with self._websession.get(f"{self._base_url}/res/output-setting", headers=self._base_header) as resp:
                data = await resp.json(content_type=None)
                zones = [[z["name"], 1, 0, 0] for z in data]
                return zones[:amount] if amount else zones
        else:
            oper_info = await self.fetch_oper_info()
            zones = oper_info.get("zones", [])
            return zones[:amount] if amount else zones

    async def fetch_device_state(self):
        """Unified state retrieval."""
        if not self._device_info:
            self._device_info = await self.fetch_device_info()
        zones = await self.fetch_zone_info()
        active_zones = await self.fetch_active_zones()
        return YardianDeviceState(zones=zones, active_zones=set(active_zones))

    async def start_irrigation(self, zone_id, duration):
        """Start irrigation with model-specific syntax."""
        if self.model_type == "yc":
            url = f"{self._base_url}/res/inst-program"
            body = {"output_durs": [[zone_id, duration]], "store": False}
        else:
            url = self._base_url
            body = {"sEvent": "AE_IRR_START_INST", "sPayload": f"[[-1, 0, 0, {zone_id}, {duration}]]"}
        await self._websession.post(url, headers=self._base_header, json=body)

    async def stop_irrigation(self):
        """Stop current irrigation."""
        if self.model_type == "yc":
            tasks = await self.fetch_active_tasks_raw()
            for t in tasks:
                stop_url = f"{self._base_url}/res/running-task/{t['id']}?action=stop"
                await self._websession.patch(stop_url, headers=self._base_header)
        else:
            await self._websession.post(self._base_url, headers=self._base_header, json={"sEvent": "AE_IRR_STOP_INST_TASK"})

    async def fetch_active_tasks_raw(self):
        """Internal helper for YC task ID management."""
        url = f"{self._base_url}/res/running-task"
        async with self._websession.get(url, headers=self._base_header) as resp:
            return await resp.json(content_type=None) if resp.status == 200 else []