from typing import TypedDict, Any

class OperationInfo(TypedDict, total=False):
    sIotcUid: str
    iTimezoneOffset: int
    fFreezePrevent: int
    iRainDelay: int
    iStandby: int
    bPopSwitch: bool
    iMasterValveId: int
    viMdArgu: list[int]
    iSensorDelay: int
    iWaterHammerDuration: int
    iAlwaysOnZoneId: int
    iScarecrowZoneId: int
    iScarecrowDurationSec: int
    DSFactor: int
    region: str
    sensor1: dict[str, Any]
    sensor2: dict[str, Any]
    zones: list[list[Any]]

class DeviceInfo(TypedDict, total=False):
    name: str
    model: str
    serialNumber: str
    yid: str
    zones: int