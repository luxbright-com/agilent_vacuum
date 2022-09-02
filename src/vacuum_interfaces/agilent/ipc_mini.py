"""
Interface to Agilent IPCMini Ion Pump Controller
"""
from enum import IntEnum, IntFlag
import logging
from typing import Optional, Union

from .communication import Command, SerialClient, LanClient, Response, parse_response
from .commands import *

logger = logging.getLogger('vacuum')

MODE_CMD = Command(win=8, writable=True, datatype=DataType.NUMERIC, description='Mode')
HV_ONOFF_CH1_CMD = Command(win=11, writable=True, datatype=DataType.LOGIC, description="HV ON/OFF CH1")
CONTROLLER_MODEL_CMD = Command(win=319, writable=False, datatype=DataType.ALPHANUMERIC, description="Controller Model")
CONTROLLER_SERIAL_NO_CMD = Command(win=323, writable=False, datatype=DataType.ALPHANUMERIC,
                                   description="Controller Serial number")
UNIT_PRESSURE_CMD = Command(win=600, writable=True, datatype=DataType.NUMERIC,
                            description="Unit pressure 0 = Torr 1=mBar (def) 2=Pa")

# TODO add missing commands
V_MEASURED_CH1_CMD = Command(win=810, writable=False, datatype=DataType.NUMERIC,
                             description="V measured CH1 [0, 7000] V: step 100V")
I_MEASURED_CH1_CMD = Command(win=811, writable=False, datatype=DataType.NUMERIC,
                             description="I measured CH1 [1E-10, 9E-1] A")
PRESSURE_CH1_CMD = Command(win=812, writable=False, datatype=DataType.NUMERIC,
                           description="Pressure CH1 [X.XE-XX]")
LABEL_CMD = Command(win=890, writable=True, datatype=DataType.ALPHANUMERIC, description="Label Max 10 char")


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


class IpcMiniDriver:
    """
    Driver for the Agilent IPC Mini Ion Pump controller
    https://www.agilent.com/en/product/vacuum-technologies/ion-pumps-controllers/ion-pump-controllers/ipcmini-ion-pump-controller
    """

    def __init__(self, com_port: Optional[str] = None, ip_address: Optional[str] = None, ip_port: int = 23,
                 addr: int = 0):
        """
        Initialize pump driver
        :param com_port: RS232 or RS485 device string
        :param ip_address: LAN interface IP address
        :param ip_port: LAN interface port (default 23)
        :param addr: controller device address for RS485 communication (default 0)
        """
        self.addr = addr
        self.pressure_unit = "unknown"
        if isinstance(com_port, str):
            self.client = SerialClient(device_str=com_port)
        elif isinstance(ip_address, str):
            self.client = LanClient(ip_address=ip_address)

    async def get_error(self) -> PumpErrorCode:
        """
        Get error code
        :return: error enum
        """
        response = await self.send_request(ERROR_CODE_CMD)
        return PumpErrorCode(int(response.data))

    async def get_status(self) -> PumpStatus:
        """
        Get pump status
        REMARK: the Agilent documentation is not correct. 0 is STOP not OK
        :return: status enum
        """
        response = await self.send_request(STATUS_CMD)
        return PumpStatus(int(response.data))

    async def send_request(self, command: Command, data: Union[bool, int, str] = None, write: bool = False,
                           **kwargs) -> Response:
        """
        Send request to controller and return a parsed response.
        :param command:
        :param data:
        :param write:
        :param kwargs:
        :return: A parsed response encoded as a Response instance
        """
        in_buff = await self.client.send(command.encode(data=data, addr=self.addr, write=write))
        logger.debug(f"response_str {in_buff}")
        return parse_response(in_buff)
