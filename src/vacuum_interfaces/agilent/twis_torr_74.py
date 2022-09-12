"""
Interface to Agilent TwisTorr 74 FS controller
"""
import asyncio
from enum import IntEnum, IntFlag
import logging
from typing import Optional, Union

from .communication import DataType, Command, SerialClient, Response, AgilentDriver, PressureUnit
from .commands import *
from .exceptions import *

logger = logging.getLogger('vacuum')

# TODO implement all commands
START_STOP_CMD = Command(win=0, writable=True, datatype=DataType.NUMERIC,
                         description="Start/Stop (in remote/ mode the window is read only)")
REMOTE_CMD = Command(win=8, writable=True, datatype=DataType.LOGIC,
                     description="Mode, Remote or Serial configuration (default = True)")
SOFT_START_CMD = Command(win=100, writable=True, datatype=DataType.LOGIC,
                         description="Soft Start (write only in Stop condition, default = False)")
# command 101 to 105 (set point) not implemented

ACTIVE_STOP_CMD = Command(win=107, writable=True, datatype=DataType.LOGIC,
                          description="Active Stop (write only in stop) 0 = NO 1 = YES")
# 108 baud rate defined in common command list
VENT_OPEN_CMD = Command(win=122, writable=True, datatype=DataType.LOGIC,
                        description="Set vent valve on/off (on = closed) On = 1 Off = 0 (default = 1)")
VENT_OPERATION_CMD = Command(win=125, writable=True, datatype=DataType.LOGIC,
                             description="Set the vent valve operation. "
                                         "Automatic = False On command = True (default = False)")
VENT_DELAY_TIME_CMD = Command(win=126, writable=True, datatype=DataType.NUMERIC,
                              description="Vent valve opening delay (expressed in 0.2sec)"
                                          "0 to 65535 (corresponding to 0 to 13107 sec)")
GAUGE_SET_POINT_TYP_CMD = Command(win=136, writable=True, datatype=DataType.NUMERIC,
                                  description="Gauge Set Point Type 0 = Freq 1 = Power 2 = Time 3 = Normal (default)")
GAUGE_SET_POINT_VALUE_CMD = Command(win=137, writable=True, datatype=DataType.NUMERIC,
                                    description="Gauge Set Point Value (Hz, W, s) (default (867)")
GAUGE_SET_POINT_MASK_CMD = Command(win=138, writable=True, datatype=DataType.NUMERIC,
                                   description="Gauge Set Point Mask (sec) (default = 0)")
GAUGE_SET_POINT_SIGNAL_TYPE_CMD = Command(win=139, writable=True, datatype=DataType.LOGIC,
                                          description="Gauge Set Point Signal Activation Type"
                                                      "False = high level active (default) True = low level active")
GAUGE_SET_POINT_HYSTERESIS_CMD = Command(win=140, writable=True, datatype=DataType.NUMERIC,
                                         description="Gauge Set front Hysteresis (in % of R2 Valve) (default = 2)")
EXTERNAL_FAN_CONFIG_CMD = Command(win=143, writable=True, datatype=DataType.NUMERIC,
                                  description="External Fan Configuration 0=ON 1=automatic 2=serial (default = 0)")
EXTERNAL_FAN_ACTIVATION_CMD = Command(win=144, writable=True, datatype=DataType.LOGIC,
                                      description="External Fan Activation 0 = OFF 1 = ON (default = 0)")
VENT_OPEN_TIME_CMD = Command(win=147, writable=True, datatype=DataType.NUMERIC,
                             description="Vent open time See “vent connector” paragraph 0 = infinite 1 bit = 0.2 sec")
POWER_LIMIT_APPLIED_CMD = Command(win=155, writable=False, datatype=DataType.NUMERIC,
                                  description="Power limit applied Read the maximum power deliverable to the pump watt")
GAS_LOAD_TYPE_CMD = Command(win=157, writable=True, datatype=DataType.NUMERIC,
                            description="Gas load type. Select the gas load to the pump 0 = N2 1 = Argon")
R1_SET_POINT_THRESHOLD_CMD = Command(win=162, writable=True, datatype=DataType.NUMERIC,
                                     description="R1 Set Point Pressure Threshold"
                                                 "Valid if min. 101 = 4 Format X.X EsXX Where X = 0 to 9 s = + or -")
PRESSURE_UNIT_CMD = Command(win=163, writable=True, datatype=DataType.NUMERIC,
                            description="Unit pressure 0=mBar 1=Pa 2=Torr")

R2_SET_POINT_TYP_CMD = Command(win=171, writable=True, datatype=DataType.NUMERIC,
                               description="R2 Set Point Type 0 = Freq 1 = Power 2 = Time 3 = Normal (default = 3) "
                                           "4 =Pressure (available only if the gauge is connected)")
R2_SET_POINT_VALUE_CMD = Command(win=172, writable=True, datatype=DataType.NUMERIC,
                                 description="R2 Set Point Value (Hz, W, s)")
R2_SET_POINT_MASK_CMD = Command(win=173, writable=True, datatype=DataType.NUMERIC,
                                description="R2 Set Point Mask (sec)")
R2_SET_POINT_SIGNAL_TYPE_CMD = Command(win=174, writable=True, datatype=DataType.LOGIC,
                                       description="R2 Set Point Signal Activation Type"
                                                   "False = high level active, True = low level active")
R2_SET_POINT_HYSTERESIS_CMD = Command(win=175, writable=True, datatype=DataType.NUMERIC,
                                      description="R2 Set front Hysteresis (in % of R2 Valve)")
R2_SET_POINT_THRESHOLD_CMD = Command(win=176, writable=True, datatype=DataType.NUMERIC,
                                     description="R2 Set Point Pressure Threshold Valid if win 171 = 4"
                                                 "Format X.X EsXX Where: X= 0 to 9 s = + or -")
START_OUTPUT_MODE_CMD = Command(win=177, writable=True, datatype=DataType.LOGIC,
                                description="Start Output Mode"
                                            "False = Starting (Output ON only with pump Status = Starting)"
                                            "True = running (Output ON when the pump is running) (default False)")
GAS_TYPE_CMD = Command(win=181, writable=True, datatype=DataType.NUMERIC,
                       description="Gas type 0 = not configured 1 = Nitrogen 2 = Argon 3 = Idrogen 4 =other")
GAS_CORRECTION_CMD = Command(win=182, writable=True, datatype=DataType.NUMERIC, description="Gas correction")
PUMP_CURRENT_CMD = Command(win=200, writable=False, datatype=DataType.NUMERIC,
                           description="Pump current in mA dc")
PUMP_VOLTAGE_CMD = Command(win=201, writable=False, datatype=DataType.NUMERIC,
                           description="Pump voltage in Vdc")
PUMP_POWER_CMD = Command(win=202, writable=False, datatype=DataType.NUMERIC,
                         description="Pump power in W (pump current x pump voltage duty cycle")
DRIVE_FREQUENCY_CMD = Command(win=203, writable=False, datatype=DataType.NUMERIC,
                              description="Driving frequency in Hz")
PUMP_TEMPERATURE_CMD = Command(win=204, writable=False, datatype=DataType.NUMERIC,
                               description="Pump temperature in °C 0 to 70")
# 205-206 defined in common command list
CONTROLLER_HEATSINK_TEMPERATURE_CMD = Command(win=211, writable=False, datatype=DataType.NUMERIC,
                                              description="Controller Heatsink Temperature (°C)")
CONTROLLER_AIR_TEMPERATURE_CMD = Command(win=216, writable=False, datatype=DataType.NUMERIC,
                                         description="Controller Air Temperature (°C)")
GAUGE_READ_CMD = Command(win=224, writable=False, datatype=DataType.NUMERIC,
                         description="Pressure reading with the format X.X E")
ROTATION_FREQUENCY_CMD = Command(win=226, writable=False, datatype=DataType.NUMERIC,
                                 description="Rotation Frequency (rpm)")

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

    def __init__(self, com_port: Optional[str] = None, addr: int = 0, **kwargs):
        super().__init__(addr=addr, **kwargs)
        self.client = SerialClient(com_port=com_port)

    async def connect(self) -> None:
        """
        Test device connection and do base configuration
        :return:
        """
        status = await self.get_status()
        errors = await self.get_error()
        logger.info(f"status:{status.name} errors: {errors.name}")

        self.is_connected = True

        for cb in self._on_connect:
            if asyncio.iscoroutinefunction(cb):
                await cb()
            else:
                cb()

    async def get_error(self) -> PumpErrorCode:
        response = await self.send_request(ERROR_CODE_CMD)
        return PumpErrorCode(int(response.data))

    async def get_status(self) -> PumpStatus:
        response = await self.send_request(STATUS_CMD)
        return PumpStatus(int(response.data))

    async def get_active_stop(self) -> bool:
        """
        Get active stop
        :return:
        """
        response = await self.send_request(ACTIVE_STOP_CMD)
        return bool(response)

    async def set_active_stop(self, enable: bool) -> None:
        """
        Set active stop.
        This is command is only allowed when stopped
        :param enable: True = active stop enabled
        :return: None
        """
        status = await self.get_status()
        if status is not PumpStatus.STOP:
            raise WinDisabled("set active stop is only allowed when pump is stopped.")
        cmd = SOFT_START_CMD
        logger.info(f"encode {enable} {cmd.encode(write=True, data=enable)}")
        await self.send_request(ACTIVE_STOP_CMD, write=True, data=enable)

    async def get_fan(self) -> bool:
        """
        Get external fan
        :return:
        """
        response = await self.send_request(EXTERNAL_FAN_ACTIVATION_CMD)
        return bool(response)

    async def set_fan(self, on: bool) -> None:
        """
        Set external fan
        :param on: on = True off = False
        :return: None
        """
        await self.send_request(EXTERNAL_FAN_ACTIVATION_CMD, write=True, data=on)

    async def get_fan_config(self) -> int:
        """
        Get external fan config
        :return: 0 = On, 1 = Auto, 2 = Serial
        """
        response = await self.send_request(EXTERNAL_FAN_CONFIG_CMD)
        return int(response)

    async def set_fan_config(self, config: int) -> None:
        """
        Configure external fan
        :param config:  0 = On, 1 = Auto, 2 = Serial
        :return: None
        """
        await self.send_request(EXTERNAL_FAN_CONFIG_CMD, write=True, data=config)

    async def read_pressure(self) -> float:
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
        return self.PRESSURE_UNITS[int(response.data)]

    async def set_pressure_unit(self, unit: PressureUnit) -> None:
        """
        Set pressure unit
        :param unit: pressure unit as PressureUnit enum
        :return: unit as PressureUnit enum
        """
        response = await self.send_request(PRESSURE_UNIT_CMD, write=True, data=self.PRESSURE_UNITS.index(unit))
        logger.debug(f"Pressure unit data {response.data}")

    async def get_soft_start(self) -> bool:
        """
        Is soft start enabled?
        :return: True if soft start is enabled, else False
        """
        response = await self.send_request(SOFT_START_CMD)
        return bool(response)

    async def set_soft_start(self, enable: bool) -> None:
        """
        Enable / Disable Soft Start. This is only allowed if when pump state is STOP
        :return:
        """
        status = await self.get_status()
        if status is not PumpStatus.STOP:
            raise WinDisabled("set soft start is only allowed when pump is stopped.")
        cmd = SOFT_START_CMD
        logger.info(f"encode {enable} {cmd.encode(write=True, data=enable)}")
        await self.send_request(SOFT_START_CMD, write=True, data=enable)

    async def get_vent_open(self) -> bool:
        """
        Get vent valve state
        :return: True if vent valve is open
        """
        response = await self.send_request(VENT_OPEN_CMD)
        return bool(response)

    async def set_vent_open(self, on: bool):
        """
        Open / close vent valve.
        This command requires vent valve operation to be True (on command).
        :param on:
        :return:
        """
        await self.send_request(VENT_OPEN_CMD, write=True, data=on)

    async def get_vent_delay_time(self) -> float:
        """
        Get vent valve opening delay time [s]
        :return: opening delay in s
        """
        response = await self.send_request(VENT_DELAY_TIME_CMD)
        return float(response) * 0.2

    async def set_vent_delay_time(self, delay: float) -> None:
        """
        Set vent valve opening delay in s [0.2 s steps]
        :param delay: delay in s
        :return:
        """
        value = int(delay / 0.2)
        await self.send_request(VENT_DELAY_TIME_CMD, write=True, data=value)

    async def get_vent_open_time(self) -> float:
        """
        Get vent valve open time in s (0=infinite)
        :return: open time in s
        """
        response = await self.send_request(VENT_OPEN_TIME_CMD)
        return float(response) * 0.2

    async def set_vent_open_time(self, open_time) -> None:
        """
        Set vent open time in s
        :param open_time: time i s
        :return: None
        """
        value = int(open_time / 0.2)
        await self.send_request(VENT_OPEN_TIME_CMD, write=True, data=value)

    async def get_vent_operation(self) -> bool:
        """
        Get vent valve operation setting.
        Automatic = False On command = True (default = False)
        :return: True = on command, False = Automatic
        """
        response = await self.send_request(VENT_OPERATION_CMD)
        return bool(response)

    async def set_vent_operation(self, on_command: bool) -> None:
        """
        Set vent valve operation.
        Automatic = False On command = True (default = False)
        :param on_command:
        :return: None
        """
        await self.send_request(VENT_OPERATION_CMD, write=True, data=on_command)

    async def start(self) -> None:
        """
        Switch on Ion pump
        :return: None
        """
        await self.send_request(START_STOP_CMD, write=True, data=True)

    async def stop(self) -> None:
        """
        Switch off Ion pump
        :return:
        """
        await self.send_request(START_STOP_CMD, write=True, data=False)
