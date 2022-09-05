"""
Interface to Agilent TwisTorr 74 FS controller
"""
import asyncio
from enum import IntEnum, IntFlag
import logging
from typing import Optional, Union

from .communication import DataType, Command, SerialClient, LanClient, Response, AgilentDriver, PressureUnit
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
EXTERNAL_FAN_CONFIG_CMD = Command(win=143, writable=True, datatype=DataType.NUMERIC,
                                  description="External Fan Configuration 0=ON 1=automatic 2=serial (default = 0)")
EXTERNAL_FAN_ACTIVATION_CMD = Command(win=144, writable=True, datatype=DataType.LOGIC,
                                      description="External Fan Activation 0 = OFF 1 = ON (default = 0)")

PRESSURE_UNIT_CMD = Command(win=163, writable=True, datatype=DataType.NUMERIC,
                            description="Unit pressure 0=mBar 1=Pa 2=Torr")
# this win code is referenced as read pressure at other parts of doc
GAUGE_READ_CMD = Command(win=224, writable=False, datatype=DataType.NUMERIC,
                         description="Pressure reading with the format X.X E")
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


class TwisTorr74Driver(AgilentDriver):
    """
    Driver for the Agilent TwisTorr 74 FS Turbomolecular pump rack controller
    """
    PRESSURE_UNITS = [PressureUnit.mBar, PressureUnit.Pa, PressureUnit.Torr]

    def __init__(self, com_port: Optional[str] = None, addr: int = 0,
                 pressure_unit: PressureUnit = PressureUnit.unknown, **kwargs):
        super().__init__(addr=addr, **kwargs)
        self.client = SerialClient(device_str=com_port)
        self.pressure_unit = pressure_unit

    async def connect(self) -> None:
        """
        Test device connection and do base configuration
        :return:
        """
        status = await self.get_status()
        errors = await self.get_error()
        logger.info(f"status:{status.name} errors: {errors.name}")

        # TODO add gauge pressure unit
        if self.pressure_unit is PressureUnit.unknown:
            await self.get_pressure_unit()
        else:
            await self.set_pressure_unit(self.pressure_unit)

        if asyncio.iscoroutinefunction(self.on_connect):
            await self.on_connect()

    async def get_error(self) -> PumpErrorCode:
        response = await self.send_request(ERROR_CODE_CMD)
        return PumpErrorCode(int(response.data))

    async def get_status(self) -> PumpStatus:
        response = await self.send_request(STATUS_CMD)
        return PumpStatus(int(response.data))

    async def get_pressure(self) -> float:
        """
        Read pressure value (in configured unit)
        :return: pressure value
        """
        response = await self.send_request(GAUGE_READ_CMD)
        return float(response.data)

    async def get_pressure_unit(self) -> PressureUnit:
        """
        Get pressure unit
        :return: pressure unit as PressureUnit enum
        """
        response = await self.send_request(PRESSURE_UNIT_CMD)
        logger.debug(f"Pressure unit data {response.data}")
        self.pressure_unit = self.PRESSURE_UNITS[int(response.data)]
        return self.pressure_unit

    async def set_pressure_unit(self, unit: PressureUnit) -> PressureUnit:
        """
        Set pressure unit
        :param unit: pressure unit as PressureUnit enum
        :return: unit as PressureUnit enum
        """
        response = await self.send_request(PRESSURE_UNIT_CMD, write=True, data=self.PRESSURE_UNITS.index(unit))
        logger.debug(f"Pressure unit data {response.data}")
        self.pressure_unit = self.PRESSURE_UNITS[int(response.data)]
        return self.pressure_unit

    async def on(self) -> None:
        """
        Switch on Ion pump
        :return: None
        """
        await self.send_request(START_STOP_CMD, write=True, data=True)

    async def off(self) -> None:
        """
        Switch off Ion pump
        :return:
        """
        await self.send_request(START_STOP_CMD, write=True, data=False)
