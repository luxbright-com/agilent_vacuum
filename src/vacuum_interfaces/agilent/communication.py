from abc import abstractmethod
import asyncio
import aioserial
from enum import Enum, IntEnum
from dataclasses import dataclass
import logging
import serial
from telnetlib import Telnet
from typing import Optional, Union

from .exceptions import *

logger = logging.getLogger('vacuum')


class PressureUnit(Enum):
    """
    Pressure Unit
    REMARK: the numerical encoding is NOT consistent among Agilent devices. Don't use this to decode request/response
    """
    unknown = 1000
    mBar = 1001
    Pa = 1002
    Torr = 1003


class ResultCode(IntEnum):
    """
    Result codes used in response messages
    """
    ACK = 0x06
    NACK = 0x15
    UNKNOWN_WINDOW = 0x32
    DATA_TYPE_ERROR = 0x33
    OUT_OF_RANGE = 0x34
    WIN_DISABLED = 0x35


@dataclass()
class Response:
    """
    Parsed response from controller
    """
    addr: int
    data: Optional[bytes] = None
    result_code: Optional[ResultCode] = None
    write: bool = False
    win: Optional[int] = None


class DataType(Enum):
    """
    Agilent Window Protocol Datatypes
    """
    LOGIC = 1
    NUMERIC = 2
    ALPHANUMERIC = 3


@dataclass(order=True, frozen=True)
class Command:
    """
    Agilent Window Protocol Command
    """
    win: int
    writable: bool
    datatype: DataType
    description: str

    @staticmethod
    def bool_str(data: Union[bool, int]) -> str:
        if isinstance(data, bool):
            return '1' if data is True else '0'
        elif isinstance(data, int):
            if data == 0:
                return '0'
            elif data == 1:
                return '1'
            else:
                raise OutOfRange("data value must be bool, 0 or 1")
        else:
            raise DataTypeError("data must be bool or int type")

    @staticmethod
    def num_str(data: Union[int, str]) -> str:
        if isinstance(data, int):
            return f"{data:06}"
        elif isinstance(data, str):
            return data
        else:
            raise DataTypeError("data must be int or str type")

    def encode(self, data: Union[bool, int, str] = None, addr: int = 0, write: bool = False) -> bytearray:
        """
        Encode message string including STX, ETX and checksum
        :param data: optional data to send
        :param addr: device address, only used for RS485, leave 0 for RS232
        :param write: write flag, Write = True, Read = False
        :return: encodes message string
        """
        addr_val = chr(addr + 0x80)
        if write is True:
            if self.writable is False:
                raise WinDisabled("Tried to write to e read only command")

            if data is None:
                raise DataTypeError(f"data was None but {self.datatype} was expected")

            if self.datatype is DataType.LOGIC:
                data_str = self.bool_str(data)
            elif self.datatype is DataType.NUMERIC:
                data_str = self.num_str(data)
            elif self.datatype is DataType.ALPHANUMERIC:
                data_str = str(data)
            else:
                raise DataTypeError()

            # <STX><ADDR><WIN><RW><DATA><ETX>
            message = f"\x02{addr_val}{self.win:03}1{data_str}\x03"
        else:
            # <STX><ADDR><WIN><RW><ETX>
            message = f"\x02{addr_val}{self.win:03}0\x03"

        # we must encode as 8 bit ascii to support the address parameter
        out_buff = bytearray(message.encode('iso-8859-1'))
        checksum = f"{calc_checksum(out_buff):x}".upper().encode('iso-8859-1')
        logger.debug(f"message {out_buff} checksum {checksum}")
        out_buff.extend(checksum)
        return out_buff


class SerialClient:
    """
    RS232 and RS485 client for communication with Pump Controllers
    """
    def __init__(self, device_str: str, baudrate: int = 9600, timeout: float = 0.1):
        """
        Initialize
        :param device_str: communication port
        :param baudrate: communication speed (default 9600)
        :param timeout: read/write timeout
        """
        self.serial = aioserial.AioSerial(port=device_str, baudrate=baudrate,
                                          stopbits=serial.STOPBITS_ONE,
                                          timeout=timeout,
                                          write_timeout=timeout)
        self.lock = asyncio.Lock()  # restrict to one reply request at a time
        logger.info(f"Serial port {device_str}")

    async def send(self, out_buff: bytes) -> bytes:
        """
        Send request and wait for reply
        :param out_buff: 8 bit ascii encoded message string including STX, ETC and checksum
        :return: response message. 8-bit ascii encoding including STX, ETX and checksum
        """
        async with self.lock:
            logger.debug(f"out_buff {out_buff}")
            sent_bytes = await self.serial.write_async(out_buff)
            logger.debug(f"sent bytes {sent_bytes}")

            # TODO add fault check

            in_buff = await self.serial.read_until_async(expected=b'/x03')
            logger.debug(f"in_buff {in_buff}")
            return in_buff


class LanClient:
    """
    Lan client for communication with pump controllers.
    Uses blocking telnet as socket.
    """
    def __init__(self, ip_address: str, ip_port: int = 23):
        self.lock = asyncio.Lock()   # restrict to one reply request at a time
        self.telnet = Telnet(ip_address, ip_port)

    async def send(self, out_buff: bytes) -> bytes:
        """
        Send request and wait for reply using telnet
        :param out_buff: 8 bit ascii encoded message string including STX, ETC and checksum
        :return: response message. 8-bit ascii encoding including STX, ETX and checksum
        """
        # TODO wrap in asyncio executors
        async with self.lock:
            self.telnet.write(out_buff)
            in_buff = self.telnet.read_until(b"\x03") + self.telnet.read_eager()
        logger.debug(f"in_buff {in_buff}")
        return in_buff


class AgilentDriver:
    """
    Base class for Agilent drivers
    """

    def __init__(self, addr: int = 0, **kwargs):
        """
        Initialize driver
        :param addr: controller device address for RS485 communication (default 0)
        """
        self.addr = addr
        self.client: Union[LanClient, SerialClient, None] = None
        self.on_connect: Optional[callable] = None

    async def connect(self) -> None:
        """
        Initialize communication and set device in known state.
        Must call async self.on_connect callback at end to allow for custom configuration
        :return:
        """
        ...

    @staticmethod
    def parse_response(buff: bytes) -> Response:
        """
        Parse response message string to extract address and data attributes
        :param buff: response message string including STX, ETX and checksum
        :return: address : int, data: str
        :raises NACK if command result was negative
        :raises UnknownWindow if hhe window specified in the command is not a valid window.
        :raises DataTypeError if the datatype does not match window requirement
        :raises OutOfRange if the value expressed during a write command is not within the range value for the window.
        :raises WinDisabled if the window specified is Read Only or is temporarily disabled.
        """
        logger.debug(f"buff {buff} has length {len(buff)}")
        end_pos = buff.find(b'\x03')
        if end_pos == -1:
            raise EOFError("Missing ETX, response message is not complete.")
        message = buff[0:end_pos]
        logger.debug(f"message {message} has length {len(message)}")
        addr = message[1] - 0x80

        if len(message) == 3:
            # ACK / NACK / ERROR
            response = Response(addr=addr, write=True, result_code=ResultCode(message[2]))
            # test response codes and raise corresponding exceptions
            if response.result_code is ResultCode.NACK:
                raise NACK
            if response.result_code is ResultCode.UNKNOWN_WINDOW:
                raise UnknownWindow
            if response.result_code is ResultCode.DATA_TYPE_ERROR:
                raise DataTypeError
            if response.result_code is ResultCode.OUT_OF_RANGE:
                raise OutOfRange
            if response.result_code is ResultCode.WIN_DISABLED:
                raise WinDisabled

        else:
            # arbitrary length data
            write = True if message[5] == 1 else False
            response = Response(addr=addr, win=int(message[2:5]), write=write, data=message[6:])
        return response

    @abstractmethod
    async def get_pressure(self) -> float:
        """
        Read pressure value (in configured unit)
        Must be implemented in concrete subclasses.
        :return: pressure value
        """

    @abstractmethod
    async def get_pressure_unit(self) -> PressureUnit:
        """
        Request pressure unit.
        Must be implemented in concrete subclasses.
        :return: PressureUnit enum
        """
        pass

    async def send_request(self, command: Command, data: Union[bool, int, str] = None, write: bool = False) -> Response:
        """
        Send request to controller and return a parsed response instance.
        :param command: Command instance
        :param data: data to send
        :param write: read/write command
        :return: A parsed response encoded as a Response instance
        """
        in_buff = await self.client.send(command.encode(data=data, addr=self.addr, write=write))
        logger.debug(f"response_str {in_buff}")
        return self.parse_response(in_buff)


def calc_checksum(message: bytes) -> int:
    """
    Calculates XOR CRC
    :param message: ascii message as bytes
    :return: checksum as int
    """
    result = 0
    # remove STX
    if message[0] == 0x02:
        message = message[1:]
    for char in message:
        result = result ^ char
    return result


def validate_checksum(message: bytes) -> bool:
    """
    Validate message with XOR CRC checksum
    :param message: ascii message bytes including 2 trailing checksum bytes
    :return: True if checksum is valid
    """
    checksum = int(message[-2:], 16)
    return calc_checksum(message[0:-2]) == checksum

