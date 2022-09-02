"""
Interface to Agilent TwisTorr 74 FS controller
"""
import asyncio
from enum import IntEnum, IntFlag
import logging
from typing import Optional, Union

from .communication import DataType, Command, SerialClient, LanClient, Response, parse_response
from .commands import *

logger = logging.getLogger('vacuum')

# TODO implement all commands
REMOTE_CMD = Command(win=8, writable=True, datatype=DataType.LOGIC,
                     description="Mode, Remote or Serial configuration (default = True)")
START_STOP_CMD = Command(win=0, writable=True, datatype=DataType.NUMERIC,
                         description="Start/Stop (in remote/ mode the window is read only)")
SOFT_START_CMD = Command(win=100, writable=True, datatype=DataType.LOGIC,
                         description="Soft Start (write only in Stop condition, default = False)")
R1_SET_POINT_TYPE_CMD = Command(win=101, writable=True, datatype=DataType.NUMERIC,
                                description="R1 Set Point type (default = 0)")
R1_SET_POINT_CMD = Command(win=102, writable=True, datatype=DataType.NUMERIC,
                           description="R1 Set Point value (expressed in Hz, W or s, default = 867)")

# this win code is referenced as read pressure at other parts of doc
GAUGE_STATUS_CMD = Command(win=257, writable=False, datatype=DataType.NUMERIC, description="Gauge status")
GAUGE_POWER_CMD = Command(win=267, writable=True, datatype=DataType.NUMERIC, description="Gauge power")


class PumpStatus(IntEnum):
    STOP = 0
    WAITING = 1
    STARTING = 2
    AUTO_TUNING = 3
    BRAKING = 4
    NORMAL = 5
    FAIL = 6


class PumpErrorCode(IntFlag):
    NO_ERROR = 0x00
    NO_CONNECTION = 0x01
    PUMP_OVERTEMP = 0x02
    CONTROLL_OVERTEMP = 0x04
    POWER_FAIL = 0x08
    AUX_FAIL = 0x10
    OVERVOLTAGE = 0x20
    SHORT_CIRCUIT = 0x40
    TOO_HIGH_LOAD = 0x80


class TwisTorr74Driver:
    """
    Driver for the Agilent TwisTorr 74 FS Turbomolecular pump rack controller
    """

    def __init__(self, com_port: Optional[str] = None, addr: int = 0):
        self.addr = addr
        self.client = SerialClient(device_str=com_port)

    async def get_error(self) -> PumpErrorCode:
        response = await self.send_request(ERROR_CODE_CMD)
        return PumpErrorCode(int(response.data))

    async def get_status(self) -> PumpStatus:
        response = await self.send_request(STATUS_CMD)
        return PumpStatus(int(response.data))

    async def send_request(self, command: Command, data: Union[bool, int, str] = None, write: bool = False,
                           **kwargs) -> Response:
        in_buff = await self.client.send(command.encode(data=data, addr=self.addr, write=write))
        logger.debug(f"response_str {in_buff}")
        return parse_response(in_buff)
