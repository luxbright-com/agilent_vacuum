import asyncio
import pytest
from vacuum_interfaces.agilent.ipc_mini import *


@pytest.mark.asyncio
async def test_send_serial_request():
    # test via RS232
    ipc_mini = IpcMiniDriver(com_port='/dev/ttyUSB0', addr=0)
    # ipc_mini.connect()
    response = await ipc_mini.send_request(STATUS_CMD)
    assert response.result_code is None


@pytest.mark.asyncio
async def test_send_lan_request():
    # test via RS232
    ipc_mini = IpcMiniDriver(ip_address="192.168.1.230", addr=0)
    # ipc_mini.connect()
    response = await ipc_mini.send_request(STATUS_CMD)
    assert response.result_code is None


@pytest.mark.asyncio
async def test_send_basic_commands():
    # test via RS232
    ipc_mini = IpcMiniDriver(ip_address="192.168.1.230", addr=0)

    status = await ipc_mini.get_status()
    logger.info(f"pump status: {status.name}")
    assert (status is PumpStatus.NORMAL) or (status is PumpStatus.STOP)

    error = await ipc_mini.get_error()
    logger.info(f"pump error: {error.name}")
    assert error is PumpErrorCode.NO_ERROR

    response = await ipc_mini.send_request(CONTROLLER_MODEL_CMD)
    logger.info(f"controller model {response.data}")
    assert len(response.data) > 4

    response = await ipc_mini.send_request(CONTROLLER_SERIAL_NO_CMD)
    logger.info(f"serial no {response.data}")
    assert len(response.data) > 4

    response = await ipc_mini.send_request(PRESSURE_CH1_CMD)
    logger.info(f"pressure {response.data} {float(response.data)}")
    assert len(response.data) > 4

    response = await ipc_mini.send_request(V_MEASURED_CH1_CMD)
    logger.info(f"voltage {response.data}")
    assert len(response.data) > 2

    response = await ipc_mini.send_request(I_MEASURED_CH1_CMD)
    logger.info(f"current {response.data}")
    assert len(response.data) > 2
