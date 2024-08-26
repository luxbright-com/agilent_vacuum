"""
Interface to Agilent TwisTorr 74 FS controller
"""
import asyncio
from collections import namedtuple
from enum import IntEnum, IntFlag
import logging
from typing import Optional, Union, NamedTuple

from .communication import DataType, Command, SerialClient, Response, AgilentDriver, PressureUnit, LanClient
from .commands import *
from .exceptions import *

logger = logging.getLogger('vacuum')

# TODO implement all commands
START_STOP_CMD = Command(win=0, writable=True, datatype=DataType.LOGIC,
                         description="Start/Stop (in remote/ mode the window is read only)")
REMOTE_CMD = Command(win=8, writable=True, datatype=DataType.LOGIC,
                     description="Mode, Remote or Serial configuration (default = True)")
SOFT_START_CMD = Command(win=100, writable=True, datatype=DataType.LOGIC,
                         description="Soft Start (write only in Stop condition, default = False)")
R1_SET_POINT_TYPE_CMD = Command(win=101, writable=True, datatype=DataType.NUMERIC,
                                description="R1 Set Point type 0 = Frequency 1 = Power 2 = Time 3 = Normal (default = 3)"
                                            "4 =Pressure (available only if the gauge is connected)")
R1_SET_POINT_VALUE_CMD = Command(win=102, writable=True, datatype=DataType.NUMERIC,
                                 description="R1 Set Point threshold value (expressed in Hz, W or s)"
                                             "(default = 900) Note, use WIN 162 for pressure")
R1_SET_POINT_DELAY_CMD = Command(win=103, writable=True, datatype=DataType.NUMERIC,
                                 description="Set Point delay: time between the pump start and the set point check"
                                             "(seconds) 0 to 99999 (default = 0)")
R1_SET_POINT_ACTIVATION_TYPE_CMD = Command(win=104, writable=True, datatype=DataType.LOGIC,
                                           description='Set Point signal activation type: the signal can be'
                                                       '"high level active" or "low level active"'
                                                       '0 = high level active 1 = low level active (default = 0)')
R1_SET_POINT_HYSTERESIS_CMD = Command(win=105, writable=True, datatype=DataType.NUMERIC,
                                      description="Set point hysteresis (in % of value) 0 to 100 (default = 2)")
ACTIVE_STOP_CMD = Command(win=107, writable=True, datatype=DataType.LOGIC,
                          description="Active Stop (write only in stop) 0 = NO 1 = YES")
WATER_COOLING_CMD = Command(win=106, writable=True, datatype=DataType.LOGIC,
                            description="Water cooling 0 = NO 1 = YES")
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
R1_SET_POINT_PRESSURE_VALUE_CMD = Command(win=162, writable=True, datatype=DataType.NUMERIC,
                                          description="R1 Set Point Pressure Threshold"
                                                      "Valid if min. 101 = 4 Format X.X EsXX Where X = 0 to 9 s = + or -")
PRESSURE_UNIT_CMD = Command(win=163, writable=True, datatype=DataType.NUMERIC,
                            description="Unit pressure 0=mBar 1=Pa 2=Torr")
ENABLE_STOP_SPEED_READ_CMD = Command(win=167, writable=True, datatype=DataType.LOGIC,
                                     description="Enable/Disable reading the pump speed after Stop command")
R2_SET_POINT_TYPE_CMD = Command(win=171, writable=True, datatype=DataType.NUMERIC,
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
R2_SET_POINT_PRESSURE_VALUE_CMD = Command(win=176, writable=True, datatype=DataType.NUMERIC,
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


class GaugeStatus(IntEnum):
    NOT_CONNECTED = 0
    CONNECTED = 1
    UNDER_RANGE = 2
    OVER_RANGE = 3
    RID_UNKNOWN = 4


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


class SetpointType(IntEnum):
    """
    R1 and R1 setpoint types.
    """
    FREQ = 0
    POWER = 1
    TIME = 2
    NORMAL = 3
    PRESSURE = 4


class SetpointTuple(NamedTuple):
    """
    R1 and R2 setpoint tuple.
    """
    point_type: SetpointType
    value: float | int
    delay: int
    active_high: bool
    hysteresis: int


class TwisTorr74Driver(AgilentDriver):
    """
    Driver for the Agilent TwisTorr 74 FS Turbomolecular pump rack controller
    """
    PRESSURE_UNITS = [PressureUnit.mBar, PressureUnit.Pa, PressureUnit.Torr]

    def __init__(self, client: Union[LanClient, SerialClient, None], addr: int = 0, **kwargs):
        super().__init__(client, addr=addr, **kwargs)

    async def connect(self, max_retries: int = 1) -> None:
        """
        Test device connection and do base configuration
        :return:
        """
        # TODO add connect fail check and retry
        retries = 0
        while self.is_connected is False:
            try:
                response = await self.send_request(STATUS_CMD, force=True)
                self.is_connected = True

            except (OSError, EOFError, ComError) as e:
                logger.debug(f"Failed to open {e}")
                if max_retries > 0:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Failed to connect to TwissTorr74")
                        raise ComError(f"Failed to connect to TwissTorr74")

                await asyncio.sleep(0.5)

        # TODO add readout of model and serial number
        logger.info(f"Connected to TwissTorr74 controller")
        status = await self.get_status()
        errors = await self.get_error()
        logger.info(f"status:{status.name} errors: {errors.name}")

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

    async def get_gauge_status(self) -> GaugeStatus:
        """
        Get Gauge status
        :return: GaugeStatus
        """
        response = await self.send_request(GAUGE_STATUS_CMD)
        return GaugeStatus(int(response.data))

    async def get_gauge_power(self) -> int:
        """
        Get gauge power
        :return:
        """
        response = await self.send_request(GAUGE_POWER_CMD)
        return int(response)

    async def set_gauge_power(self, value: int) -> None:
        """
        Enable / disable gauge power
        :param value: 0 = gauge off, 1= gauge on
        :return: None
        """
        await self.send_request(GAUGE_POWER_CMD, write=True, data=value)

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

    async def enable_stop_speed_reading(self, enable: bool) -> None:
        """
        Stop speed reading Activates / deactivates the pump speed reading after Stop command
        :return:
        """
        await self.send_request(ENABLE_STOP_SPEED_READ_CMD, write=True, data=enable)

    async def read_turbo_speed(self) -> float:
        """
        Read the turbo speed in RPM
        :return: turbo speed in RPM
        """
        response = await self.send_request(ROTATION_FREQUENCY_CMD)
        return float(response)

    async def read_turbo_temp(self) -> float:
        """
        Read the turbo temperature in °C
        :return: turbo temperature
        """
        response = await self.send_request(PUMP_TEMPERATURE_CMD)
        return float(response)

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
        logger.info("Driver: Start Turbo Pump")
        await self.send_request(START_STOP_CMD, write=True, data=True)

    async def stop(self) -> None:
        """
        Switch off Ion pump
        :return:
        """
        logger.info("Driver: Stop Turbo Pump")
        await self.send_request(START_STOP_CMD, write=True, data=False)

    async def get_setpoint(self, setpoint_num: int) -> SetpointTuple:
        match setpoint_num:
            case 1:
                response = await self.send_request(R1_SET_POINT_TYPE_CMD)
                s_type = SetpointType(int(response))
                response = await self.send_request(R1_SET_POINT_HYSTERESIS_CMD)
                s_hysteresis = int(response)
                response = await self.send_request(R1_SET_POINT_DELAY_CMD)
                s_delay = int(response)
                response = await self.send_request(R1_SET_POINT_ACTIVATION_TYPE_CMD)
                s_activation_high = bool(response)
                if s_type == SetpointType.PRESSURE:
                    response = await self.send_request(R1_SET_POINT_PRESSURE_VALUE_CMD)
                    s_value = float(response)
                else:
                    response = await self.send_request(R1_SET_POINT_VALUE_CMD)
                    s_value = int(response)
                return SetpointTuple(
                    point_type=s_type,
                    value=s_value,
                    delay=s_delay,
                    hysteresis=s_hysteresis,
                    active_high=s_activation_high
                )

            case 2:
                response = await self.send_request(R2_SET_POINT_TYPE_CMD)
                s_type = SetpointType(int(response))
                response = await self.send_request(R2_SET_POINT_HYSTERESIS_CMD)
                s_hysteresis = int(response)
                response = await self.send_request(R2_SET_POINT_MASK_CMD)
                s_delay = int(response)
                response = await self.send_request(R2_SET_POINT_SIGNAL_TYPE_CMD)
                s_activation_high = bool(response)
                if s_type == SetpointType.PRESSURE:
                    response = await self.send_request(R2_SET_POINT_PRESSURE_VALUE_CMD)
                    s_value = float(response)
                else:
                    response = await self.send_request(R2_SET_POINT_VALUE_CMD)
                    s_value = int(response)
                return SetpointTuple(
                    point_type=s_type,
                    value=s_value,
                    delay=s_delay,
                    hysteresis=s_hysteresis,
                    active_high=s_activation_high
                )

            case _:
                raise UnknownWindow("Setpoint number must be 1 or 2")

    async def set_setpoint(
            self,
            setpoint_num: int,
            setpoint_tuple: SetpointTuple | None = None,
            point_type: SetpointType | None = None,
            value: int | float | None = None,
            delay: int | None = None,
            active_high: bool | None = None,
            hysteresis: int | None = None,
    ) -> None:
        """
        Configure the R1 setpoint output.
        :param setpoint_num: 1 for R1 or 2 for R2
        :param setpoint_tuple: Setpoint tuple as alternative parameter.
        :param point_type: FREQ, POWER, TIME, NORMAL (default) or PRESSURE.
        :param value: Setpoint value.
        :param delay: Time between the pump start and the set point check (seconds) 0 to 99999 (default = 0).
        :param active_high: Signal active state (low or high).
        :param hysteresis: Hysteresis in persent 0-100.
        :return: None
        """
        if isinstance(setpoint_tuple, SetpointTuple):
            point_type = setpoint_tuple.point_type
            value = setpoint_tuple.value
            delay = setpoint_tuple.delay
            active_high = setpoint_tuple.active_high
            hysteresis = setpoint_tuple.hysteresis

        if point_type is None:
            raise UnknownWindow("Setpoint type must be defined")

        match setpoint_num:
            case 1:
                await self.send_request(R1_SET_POINT_TYPE_CMD, write=True, data=point_type.value)

                if value is not None:
                    if point_type is SetpointType.PRESSURE:
                        await self.send_request(R1_SET_POINT_PRESSURE_VALUE_CMD, write=True, data=value)
                    else:
                        await self.send_request(R1_SET_POINT_VALUE_CMD, write=True, data=int(value))

                if isinstance(delay, int):
                    await self.send_request(R1_SET_POINT_DELAY_CMD, write=True, data=delay)
                if isinstance(active_high, bool):
                    await self.send_request(R1_SET_POINT_ACTIVATION_TYPE_CMD, write=True, data=active_high)
                if isinstance(hysteresis, int):
                    await self.send_request(R1_SET_POINT_HYSTERESIS_CMD, write=True, data=hysteresis)

            case 2:
                await self.send_request(R2_SET_POINT_TYPE_CMD, write=True, data=point_type.value)

                if value is not None:
                    if point_type is SetpointType.PRESSURE:
                        await self.send_request(R2_SET_POINT_PRESSURE_VALUE_CMD, write=True, data=value)
                    else:
                        await self.send_request(R2_SET_POINT_VALUE_CMD, write=True, data=int(value))

                if isinstance(delay, int):
                    await self.send_request(R2_SET_POINT_MASK_CMD, write=True, data=delay)
                if isinstance(active_high, bool):
                    await self.send_request(R2_SET_POINT_SIGNAL_TYPE_CMD, write=True, data=active_high)
                if isinstance(hysteresis, int):
                    await self.send_request(R2_SET_POINT_HYSTERESIS_CMD, write=True, data=hysteresis)

            case _:
                raise UnknownWindow("Setpoint number must be 1 or 2")
