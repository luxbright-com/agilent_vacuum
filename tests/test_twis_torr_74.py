import asyncio
import pytest
from vacuum_interfaces.agilent.twis_torr_74 import *


@pytest.mark.asyncio
async def test_send_request():
    # test via RS232
    pump = TwisTorr74Driver(com_port='/dev/ttyUSB0', addr=0)
    # ipc_mini.connect()
    response = await pump.send_request(STATUS_CMD)
    assert response.result_code is None


@pytest.mark.asyncio
async def test_send_basic_commands():
    # test via RS232
    pump = TwisTorr74Driver(com_port='/dev/ttyUSB0', addr=0)

    status = await pump.get_status()
    assert status is PumpStatus.STOP

    error = await pump.get_error()
    assert error is PumpErrorCode.NO_ERROR
