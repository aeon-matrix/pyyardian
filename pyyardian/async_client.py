import logging
import aiohttp
import asyncio
from dataclasses import dataclass

from .const import MODEL_DETAIL, DEFAULT_TIMEOUT
from .exceptions import NotAuthorizedException, NetworkException
from .typing import DeviceInfo, OperationInfo

_LOGGER = logging.getLogger(__name__)


@dataclass
class YardianDeviceState:
    """Data retrieved from a Yardian device."""

    zones: list[list]
    active_zones: set[int]


class AsyncYardianClient:
    def __init__(
        self,
        websession: aiohttp.ClientSession,
        host: str,
        token: str = None,
    ) -> None:
        """Initialize the client. Use .create() for async auto-detection."""
        self._websession = websession
        self._host = host
        self._token = token  # Static token for YP
        self._base_url = f"http://{host}:880"
        self._base_header = {}
        self._device_info = None
        self.model_type = "yp"

    @classmethod
    async def create(
        cls,
        websession: aiohttp.ClientSession,
        host: str,
        token: str = None,
    ):
        """Asynchronous factory to create a client and auto-detect the model."""
        # FIX 1: Removed username and password from the class initialization
        client = cls(websession, host, token)
        await client.detect_model()
        return client

    async def detect_model(self):
        """Identify YP or YC by reading the model string via API_GET_DEVICEINFO."""
        # We now expect a token for both platforms
        headers = {"Yardian-Token": self._token} if self._token else {}
        url = f"http://{self._host}:880/API_GET_DEVICEINFO"

        try:
            async with self._websession.get(
                url, headers=headers, timeout=DEFAULT_TIMEOUT
            ) as resp:
                data = await resp.json(content_type=None)

                # Check if the device rejected the request (e.g., missing or invalid token)
                if data and data.get("iCode") == -1000:
                    raise NotAuthorizedException("Invalid token or missing token.")

                # Extract the model string (handle 'result' dictionary wrapping if present)
                result = data.get("result", data)
                model = result.get("model", "")

                # Future-proof check: Is the last part a 'C' followed by a number? (e.g., C1, C2)
                is_yc_model = (
                    len(model) >= 2 and model[-2].upper() == "C" and model[-1].isdigit()
                )

                # FIX 2: Simplified logic completely for Option 1 (No login_yc fallback)
                if is_yc_model:
                    self.model_type = "yc"
                    self._base_url = f"http://{self._host}:80"
                else:
                    self.model_type = "yp"
                    self._base_url = f"http://{self._host}:880"

                # Both YC and YP now use the exact same header format!
                if self._token:
                    self._base_header = {"Yardian-Token": self._token}
                else:
                    raise NotAuthorizedException("A token is required for all models.")

        except NotAuthorizedException:
            raise
        except Exception as e:
            raise NetworkException(str(e))

    async def fetch_device_info(self) -> DeviceInfo:
        """Fetch model info on Port 880."""
        url = f"http://{self._host}:880/API_GET_DEVICEINFO"
        try:
            async with self._websession.get(
                url, headers=self._base_header, timeout=DEFAULT_TIMEOUT
            ) as response:
                resp = await response.json(content_type=None)

                if resp is None:
                    _LOGGER.error(
                        "Controller at %s returned empty response during info fetch",
                        self._host,
                    )
                    return {}

                result = resp.get("result", resp)
                model = result.get("model")
                return result | MODEL_DETAIL.get(model, {})
        except Exception:
            raise NetworkException()

    async def fetch_oper_info(self) -> OperationInfo:
        """Route to correct info endpoint."""
        endpoint = (
            "/res/controller" if self.model_type == "yc" else "/API_MGR_GET_OPERINFO"
        )
        async with self._websession.get(
            f"{self._base_url}{endpoint}", headers=self._base_header
        ) as response:
            resp = await response.json(content_type=None)

            if resp is None:
                _LOGGER.error(
                    "Controller at %s returned empty response during oper fetch",
                    self._host,
                )
                return {}
            return resp.get("result", resp)

    async def fetch_active_zones(self):
        """Fetch currently running zone IDs."""
        endpoint = (
            "/res/running-task"
            if self.model_type == "yc"
            else "/API_ZONE_GET_OPENINGZONE"
        )
        async with self._websession.get(
            f"{self._base_url}{endpoint}", headers=self._base_header
        ) as response:
            resp = await response.json(content_type=None)

            if resp is None:
                return []

            if self.model_type == "yc":
                return [task["output_id"] for task in resp]
            return resp.get("result", [])

    async def fetch_zone_info(self, amount=None):
        """Fetch zone metadata (names and status)."""
        if self.model_type == "yc":
            async with self._websession.get(
                f"{self._base_url}/res/output-setting", headers=self._base_header
            ) as resp:
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
        """Start irrigation with model-specific syntax. All durations are converted to seconds."""
        # Convert the minutes provided by HA into seconds for the hardware
        api_duration = duration * 60

        if self.model_type == "yc":
            # Standalone C1 / YC Logic
            url = f"{self._base_url}/res/inst-program"
            body = {"output_durs": [[zone_id, api_duration]], "store": False}
        else:
            # Yardian Pro / YP Logic (Port 880)
            # Even on YP, the 'Instant' payload expects seconds for precision
            url = self._base_url
            body = {
                "sEvent": "AE_IRR_START_INST",
                "sPayload": f"[[-1, 0, 0, {zone_id}, {api_duration}]]",
            }

        await self._websession.post(url, headers=self._base_header, json=body)

    async def stop_irrigation(self):
        """Stop current irrigation."""
        if self.model_type == "yc":
            tasks = await self.fetch_active_tasks_raw()
            for t in tasks:
                stop_url = f"{self._base_url}/res/running-task/{t['id']}?action=stop"
                await self._websession.patch(stop_url, headers=self._base_header)
        else:
            await self._websession.post(
                self._base_url,
                headers=self._base_header,
                json={"sEvent": "AE_IRR_STOP_INST_TASK"},
            )

    async def stop_zone(self, zone_id: int):
        """Stop irrigation for a specific zone."""
        if self.model_type == "yc":
            tasks = await self.fetch_active_tasks_raw()
            for t in tasks:
                if t.get("output_id") == zone_id:
                    stop_url = (
                        f"{self._base_url}/res/running-task/{t['id']}?action=stop"
                    )
                    await self._websession.patch(stop_url, headers=self._base_header)
                    break
        else:
            await self.stop_irrigation()

    async def fetch_active_tasks_raw(self):
        """Internal helper for YC task ID management."""
        url = f"{self._base_url}/res/running-task"
        async with self._websession.get(url, headers=self._base_header) as resp:
            return await resp.json(content_type=None) if resp.status == 200 else []
