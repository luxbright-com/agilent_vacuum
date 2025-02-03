"""
Interface to Agilent IPCMini Ion Pump Controller
"""

import asyncio
from enum import IntEnum, IntFlag
import logging

from .communication import SerialClient, AgilentDriver, PressureUnit
from .commands import Command, DataType
from .commands import STATUS_CMD, ERROR_CODE_CMD
from .exceptions import ComError, WinDisabled

logger = logging.getLogger("vacuum")

MODE_CMD = Command(win=8, writable=True, datatype=DataType.NUMERIC, description="Mode")
HV_ONOFF_CH1_CMD = Command(
    win=11, writable=True, datatype=DataType.LOGIC, description="HV ON/OFF CH1"
)
CONTROLLER_MODEL_CMD = Command(
    win=319,
    writable=False,
    datatype=DataType.ALPHANUMERIC,
    description="Controller Model",
)
CONTROLLER_SERIAL_NO_CMD = Command(
    win=323,
    writable=False,
    datatype=DataType.ALPHANUMERIC,
    description="Controller Serial number",
)
UNIT_PRESSURE_CMD = Command(
    win=600,
    writable=True,
    datatype=DataType.NUMERIC,
    description="Unit pressure 0 = Torr 1=mBar (def) 2=Pa",
)
AUTO_START_CMD = Command(
    win=601,
    writable=True,
    datatype=DataType.LOGIC,
    description="Autostart 0 = Disabled, 1 = Enabled",
)
PROTECT_CMD = Command(
    win=602,
    writable=True,
    datatype=DataType.LOGIC,
    description="Protect 0 = Disabled, 1 = Enabled",
)
STEP_CMD = Command(
    win=603,
    writable=True,
    datatype=DataType.LOGIC,
    description="Fixed/Step 0 = Disabled, 1 = Enabled",
)
DEVICE_NUM_CH1_CMD = Command(
    win=610, writable=True, datatype=DataType.NUMERIC, description="Device Number CH1"
)
MAX_POWER_CMD = Command(
    win=612, writable=True, datatype=DataType.NUMERIC, description="Max Power 10W – 40W"
)
V_TARGET_CH1_CMD = Command(
    win=613,
    writable=True,
    datatype=DataType.NUMERIC,
    description="V target CH1 [3000,7000] V def=7000",
)
I_PROTECT_CH1_CMD = Command(
    win=614,
    writable=True,
    datatype=DataType.NUMERIC,
    description="I protect CH1 [1,10000 uA] step 1 uA",
)
SET_POINT_CH1_CMD = Command(
    win=615,
    writable=True,
    datatype=DataType.NUMERIC,
    description="Set Point CH1 [X.XE-XX]",
)
TEMPERATURE_POWER_CMD = Command(
    win=800,
    writable=False,
    datatype=DataType.NUMERIC,
    description="Temperature Power section [0, 200] °C",
)
TEMPERATURE_CONTROLLER_CMD = Command(
    win=801,
    writable=False,
    datatype=DataType.NUMERIC,
    description="Temperature internal controller [0, 200] °C",
)
STATUS_SET_POINT = Command(
    win=804,
    writable=False,
    datatype=DataType.LOGIC,
    description="804 R L Status Set point 0 = OFF 1 = ON",
)
V_MEASURED_CH1_CMD = Command(
    win=810,
    writable=False,
    datatype=DataType.NUMERIC,
    description="V measured CH1 [0, 7000] V: step 100V",
)
I_MEASURED_CH1_CMD = Command(
    win=811,
    writable=False,
    datatype=DataType.NUMERIC,
    description="I measured CH1 [1E-10, 9E-1] A",
)
PRESSURE_CH1_CMD = Command(
    win=812,
    writable=False,
    datatype=DataType.NUMERIC,
    description="Pressure CH1 [X.XE-XX]",
)
LABEL_CMD = Command(
    win=890,
    writable=True,
    datatype=DataType.ALPHANUMERIC,
    description="Label Max 10 char",
)


class PumpStatus(IntEnum):
    """
    Ion Pump controller status codes
    REMARK: the Agilent documentation is not correct. 0 is STOP not OK
    """

    STOP = 0
    NORMAL = 5
    FAIL = 6


class PumpErrorCode(IntFlag):
    """
    Ion pump controller error codes
    """

    NO_ERROR = 0x00
    OVER_TEMPERATURE = 0x04
    INTERLOCK_CABLE = 0x20
    SHORT_CIRCUIT = 0x40
    PROTECT = 0x80


class IpcMiniDriver(AgilentDriver):
    """
    Driver for the Agilent IPC Mini Ion Pump controller
    https://www.agilent.com/en/product/vacuum-technologies/ion-pumps-controllers/ion-pump-controllers/ipcmini-ion-pump-controller
    """

    PRESSURE_UNITS = [PressureUnit.Torr, PressureUnit.mBar, PressureUnit.Pa]

    def __init__(self, client: SerialClient, addr: int = 0, **kwargs):
        """
        Initialize pump driver
        :param com_port: RS232 or RS485 device string
        :param host: LAN interface IP address
        :param port: LAN interface port (default 23)
        :param addr: controller device address for RS485 communication (default 0)
        """
        super().__init__(client, addr=addr, **kwargs)

    async def connect(self, max_retries: int = 1) -> None:
        """
        Test device connection and do base configuration
        :return: None
        """
        retries = 0
        while self.is_connected is False:
            try:
                # self.client.open()
                response = await self.send_request(STATUS_CMD, force=True)
                logger.info(f"IPC mini connected {self.client.port}")
                self.is_connected = True
            except (OSError, EOFError, ComError) as e:
                logger.debug(f"Failed to open {e}")
                if max_retries > 0:
                    retries += 1
                    if retries > max_retries:
                        logger.error("Failed to connect to IPC Mini")
                        raise ComError("Failed to connect to IPC Mini")

                await asyncio.sleep(0.5)

        logger.info("Connecting to IpcMini Ion pump controller")
        response = await self.send_request(CONTROLLER_MODEL_CMD)
        model = response.data
        response = await self.send_request(CONTROLLER_SERIAL_NO_CMD)
        serial_no = response.data
        response = await self.send_request(LABEL_CMD)
        label = response.data
        logger.info(
            f"Connected to IpcMini controller model:{model} serial_no:{serial_no} label:{label}"
        )

        response = await self.send_request(MODE_CMD)
        if int(response) == 1:
            logger.warning("Ipc Mini is in Remote mode. Software control is blocked")
        elif int(response) == 2:
            logger.warning("Ipc Mini is in Local mode. Software control is blocked")

        status = await self.get_status()
        errors = await self.get_error()
        logger.info(f"status:{status.name} errors: {errors.name}")

        for cb in self._on_connect:
            if asyncio.iscoroutinefunction(cb):
                await cb()
            else:
                cb()

    async def get_error(self) -> PumpErrorCode:
        """
        Get error code
        :return: error enum
        """
        response = await self.send_request(ERROR_CODE_CMD)
        return PumpErrorCode(int(response))

    async def get_status(self) -> PumpStatus:
        """
        Get pump status
        REMARK: the Agilent documentation is not correct. 0 is STOP not OK
        :return: status enum
        """
        response = await self.send_request(STATUS_CMD)
        return PumpStatus(int(response))

    async def read_pressure(self) -> float:
        """
        Read pressure value (in configured unit)
        :return: pressure value
        """
        try:
            response = await self.send_request(PRESSURE_CH1_CMD)
            return float(response)
        except EOFError:
            logger.warning("Read pressure failed. EOFError")
        except WinDisabled:
            logger.warning("Read pressure failed. WinDisabled")

    async def get_autostart(self) -> bool:
        """
        Read auto start setting
        :return: True if autostart is enabled, else False
        """
        response = await self.send_request(AUTO_START_CMD)
        return bool(response)

    async def read_current(self) -> float:
        """
        Read current measurement
        :return: current in A
        """
        response = await self.send_request(I_MEASURED_CH1_CMD)
        return float(response)

    async def get_current_protect(self) -> float:
        """
        Get current protect setting
        :return: current limit in mA
        """
        response = await self.send_request(I_PROTECT_CH1_CMD)
        return float(response) / 1000.0

    async def set_current_protect(self, current: float) -> None:
        """
        Set current protect setting
        :param current: [0.001 - 10] mA
        :return: None
        """
        data = int(current * 1000)
        await self.send_request(I_PROTECT_CH1_CMD, write=True, data=data)

    async def set_autostart(self, enabled: bool = False) -> None:
        """
        Set autostart setting
        :param enabled: True to enable autostart
        :return: None
        """
        await self.send_request(AUTO_START_CMD, write=True, data=enabled)

    async def get_device_num(self) -> int:
        """
        Get device number (see use guide for interpretation)
        :return: device numer as int 0-20
        """
        response = await self.send_request(DEVICE_NUM_CH1_CMD)
        return int(response)

    async def set_device_num(self, device_num: int) -> None:
        """
        Set device number (see use guide for interpretation)
        :param device_num: 0-20 (device model)
        :return: None
        """
        await self.send_request(DEVICE_NUM_CH1_CMD, write=True, data=device_num)

    async def get_pressure_unit(self) -> PressureUnit:
        """
        Get pressure unit
        :return: pressure unit as PressureUnit enum
        :raises NACK if command result was negative
        :raises UnknownWindow if hhe window specified in the command is not a valid window.
        :raises DataTypeError if the datatype does not match window requirement
        :raises OutOfRange if the value expressed during a write command is not within the range value for the window.
        :raises WinDisabled if the window specified is Read Only or is temporarily disabled.
        """
        response = await self.send_request(UNIT_PRESSURE_CMD)
        return self.PRESSURE_UNITS[int(response)]

    async def set_pressure_unit(self, unit: PressureUnit) -> None:
        """
        Set pressure unit
        :param unit: pressure unit as PressureUnit enum
        :return: unit as PressureUnit enum
        :raises NACK if command result was negative
        :raises UnknownWindow if hhe window specified in the command is not a valid window.
        :raises DataTypeError if the datatype does not match window requirement
        :raises OutOfRange if the value expressed during a write command is not within the range value for the window.
        :raises WinDisabled if the window specified is Read Only or is temporarily disabled.
        """
        data = self.PRESSURE_UNITS.index(unit)
        await self.send_request(UNIT_PRESSURE_CMD, write=True, data=data)

    async def get_protect(self) -> bool:
        """
        Read protect setting
        :return: True if protect is enabled, else False
        """
        response = await self.send_request(PROTECT_CMD)
        return bool(response)

    async def set_protect(self, enabled: bool = False) -> None:
        """
        Set protect setting
        :param enabled: True to enable autostart
        :return: None
        """
        await self.send_request(PROTECT_CMD, write=True, data=enabled)

    async def get_step(self) -> bool:
        """
        Read step setting
        :return: True if step is enabled, else False
        """
        response = await self.send_request(STEP_CMD)
        return bool(response)

    async def set_step(self, enabled: bool = False) -> None:
        """
        Set step setting
        :param enabled: True to enable step
        :return: None
        """
        await self.send_request(STEP_CMD, write=True, data=enabled)

    async def get_v_target(self) -> int:
        """
        Get target voltage CH1 [3000 - 7000] V
        :return: voltage
        """
        response = await self.send_request(V_TARGET_CH1_CMD)
        return int(response)

    async def set_v_target(self, voltage: int) -> None:
        """
        Set target voltage CH1 [3000 - 7000] V
        :param voltage: [3000 - 7000] V
        :return: None
        """
        await self.send_request(V_TARGET_CH1_CMD, write=True, data=voltage)

    async def read_voltage(self) -> int:
        """
        Read measured voltage
        :return:
        """
        response = await self.send_request(V_MEASURED_CH1_CMD)
        return int(response)

    async def read_controller_temp(self) -> float:
        """
        Read controller internal temperature
        :return:
        """
        response = await self.send_request(TEMPERATURE_CONTROLLER_CMD)
        return float(response) / 10.0

    async def read_power_temp(self) -> float:
        """
        Read controller power unit temperature
        :return:
        """
        response = await self.send_request(TEMPERATURE_POWER_CMD)
        return float(response) / 10.0

    async def start(self) -> None:
        """
        Switch on Ion pump
        :return: None
        :raises NACK if command result was negative
        :raises UnknownWindow if hhe window specified in the command is not a valid window.
        :raises DataTypeError if the datatype does not match window requirement
        :raises OutOfRange if the value expressed during a write command is not within the range value for the window.
        :raises WinDisabled if the window specified is Read Only or is temporarily disabled.
        """
        await self.send_request(HV_ONOFF_CH1_CMD, write=True, data=True)

    async def stop(self) -> None:
        """
        Switch off Ion pump
        :return: None
        """
        await self.send_request(HV_ONOFF_CH1_CMD, write=True, data=False)
