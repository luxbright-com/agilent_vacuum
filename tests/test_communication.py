import logging
import pytest
from vacuum_interfaces.agilent import calc_checksum, validate_checksum, parse_response
from vacuum_interfaces.agilent import Command, DataType, ResultCode
from vacuum_interfaces.agilent.exceptions import *

logger = logging.getLogger("test")


def test_calc_checksum():
    # test using example from start command in user guide
    test_str = b"\x8000011\x03"
    assert calc_checksum(test_str) == 0xB3

    # test that STX char at start is ignored
    test_str = b"\x02\x8000011\x03"
    assert calc_checksum(test_str) == 0xB3


def test_validate_checksum():
    test_str = b"\x8000011\x03B3"
    assert validate_checksum(test_str) is True

    test_str = b"\x8000011\x03AB"
    assert validate_checksum(test_str) is False


def test_parse_response():
    # incomplete response
    with pytest.raises(EOFError):
        test_str = b"\x02\x80\x15"
        response = parse_response(test_str)

    # ACK
    test_str = b"\x02\x80\x06\x03\x38\x35"
    assert validate_checksum(test_str) is True
    response = parse_response(test_str)
    assert response.addr == 0
    assert response.result_code == ResultCode.ACK

    # pump status
    test_str = b"\x02\x83\x32\x30\x35\x30\x30\x30\x30\x30\x30\x30\x03\x38\x37"
    assert validate_checksum(test_str) is True
    response = parse_response(test_str)
    assert response.addr == 3
    assert response.data == b"000000"
    assert response.win == 205
    assert response.write is False

    # read serial type
    test_str = b"\x02\x83\x35\x30\x34\x30\x31\x03\x42\x30"
    assert validate_checksum(test_str) is True
    response = parse_response(test_str)
    assert response.addr == 3
    assert response.data == b"1"
    assert response.write is False

    # skipped checksum in tests below
    with pytest.raises(NACK):
        test_str = b"\x02\x80\x15\x03"
        response = parse_response(test_str)

    with pytest.raises(UnknownWindow):
        test_str = b"\x02\x80\x32\x03"
        response = parse_response(test_str)

    with pytest.raises(DataTypeError):
        test_str = b"\x02\x80\x33\x03"
        response = parse_response(test_str)

    with pytest.raises(OutOfRange):
        test_str = b"\x02\x80\x34\x03"
        response = parse_response(test_str)

    with pytest.raises(WinDisabled):
        test_str = b"\x02\x80\x35\x03"
        response = parse_response(test_str)


def test_command_encode():
    # use samples from TwissTorr 74 On-board controller
    status_cmd = Command(win=205, writable=False, datatype=DataType.NUMERIC, description="Pump Status")
    with pytest.raises(WinDisabled):
        status_cmd.encode(addr=3, write=True, data=5)
    message = status_cmd.encode(addr=3)
    logger.debug(f"message {message}")
    assert validate_checksum(message) is True
    assert message == b"\x02\x83\x32\x30\x35\x30\x03\x38\x37"

    status_cmd = Command(win=0, datatype=DataType.LOGIC, writable=True, description="Start/Stop")
    start_message = status_cmd.encode(addr=0, write=True, data=True)
    assert start_message == b"\x02\x80\x30\x30\x30\x31\x31\x03\x42\x33"

    stop_cmd = Command(win=0, datatype=DataType.LOGIC, writable=True, description="Start/Stop")
    stop_message = stop_cmd.encode(addr=0, write=True, data=False)
    assert stop_message == b"\x02\x80\x30\x30\x30\x31\x30\x03\x42\x32"

    # numerical write
    unit_cmd = Command(win=163, datatype=DataType.NUMERIC, writable=True,
                       description="Pressure unit of measure 0 = mBar 1 = Pa 2 = Torr")
    unit_message = unit_cmd.encode(write=True, data=2)
    assert unit_message == b"\x02\x80\x31\x36\x33\x31000002\x0384"

    # text write
    label_cmd = Command(win=890, datatype=DataType.ALPHANUMERIC, writable=True,
                        description="Label Max 10 char")
    label_message = label_cmd.encode(write=True, data="Test")
    assert label_message == b"\x02\x80890\x31Test\x03B5"
