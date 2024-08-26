import asyncio
import logging
import pytest
from vacuum_interfaces.agilent.twis_torr_74 import *

COM_PORT = '/dev/ttyS0'
ADDR = 1

logger = logging.getLogger('vacuum')


@pytest.fixture(scope='function')
async def pump():
    client = SerialClient(com_port=COM_PORT)
    ctrl = TwisTorr74Driver(client, addr=ADDR)
    await ctrl.connect(max_retries=1)
    yield ctrl
    client.close()


@pytest.mark.asyncio
async def test_serial_request(pump):
    response = await pump.send_request(STATUS_CMD, force=True)
    assert response.result_code is None


@pytest.mark.asyncio
async def test_repeated_serial_request(pump):
    for i in range(10):
        logger.info(f"Repeated send {i}")
        response = await pump.send_request(STATUS_CMD, force=True)
        assert response.result_code is None
        await asyncio.sleep(0.2)


@pytest.mark.asyncio
async def test_send_basic_commands(pump):
    response = await pump.send_request(STATUS_CMD)
    logger.debug(f"STATUS_CMD {response.data}")

    response = await pump.send_request(ERROR_CODE_CMD)
    logger.debug(f"ERROR_CODE_CMD {response.data}")

    response = await pump.send_request(START_STOP_CMD)
    logger.debug(f"START_STOP_CMD {response.data}")
    assert bool(response) is False

    response = await pump.send_request(REMOTE_CMD)
    logger.debug(f"REMOTE_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(SOFT_START_CMD)
    logger.debug(f"SOFT_START_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(ACTIVE_STOP_CMD)
    logger.debug(f"ACTIVE_STOP_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(VENT_OPEN_CMD)
    logger.debug(f"VENT_VALVE_OPEN_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(VENT_OPERATION_CMD)
    logger.debug(f"VENT_VALVE_OPERATION_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(VENT_DELAY_TIME_CMD)
    logger.debug(f"VENT_VALVE_OPENING_DELAY_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(GAUGE_SET_POINT_TYP_CMD)
    logger.debug(f"GAUGE_SET_POINT_TYP_CMD {response.data}")
    # assert int(response) == 3

    response = await pump.send_request(GAUGE_SET_POINT_VALUE_CMD)
    logger.debug(f"GAUGE_SET_POINT_TYP_CMD {response.data}")
    # assert int(response) == 867

    response = await pump.send_request(GAUGE_SET_POINT_MASK_CMD)
    logger.debug(f"GAUGE_SET_POINT_MASK_CMD {response.data}")
    # assert int(response) == 867

    response = await pump.send_request(GAUGE_SET_POINT_SIGNAL_TYPE_CMD)
    logger.debug(f"GAUGE_SET_POINT_SIGNAL_TYPE_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(GAUGE_SET_POINT_HYSTERESIS_CMD)
    logger.debug(f"GAUGE_SET_POINT_HYSTERESIS_CMD {response.data}")
    # assert int(response) == 2

    response = await pump.send_request(EXTERNAL_FAN_CONFIG_CMD)
    logger.debug(f"EXTERNAL_FAN_CONFIG_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(EXTERNAL_FAN_CONFIG_CMD)
    logger.debug(f"EXTERNAL_FAN_CONFIG_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(VENT_OPEN_TIME_CMD)
    logger.debug(f"VENT_OPEN_TIME_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(POWER_LIMIT_APPLIED_CMD)
    logger.debug(f"POWER_LIMIT_APPLIED_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(GAS_LOAD_TYPE_CMD)
    logger.debug(f"GAS_LOAD_TYPE_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(R1_SET_POINT_VALUE_CMD)
    logger.debug(f"R1_SET_POINT_THRESHOLD_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(PRESSURE_UNIT_CMD)
    logger.debug(f"PRESSURE_UNIT_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(R2_SET_POINT_TYPE_CMD)
    logger.debug(f"R2_SET_POINT_TYP_CMD {response.data}")
    # assert int(response) == 3

    response = await pump.send_request(R2_SET_POINT_VALUE_CMD)
    logger.debug(f"R2_SET_POINT_TYP_CMD {response.data}")
    # assert int(response) == 867

    response = await pump.send_request(R2_SET_POINT_MASK_CMD)
    logger.debug(f"R2_SET_POINT_MASK_CMD {response.data}")
    # assert int(response) == 867

    response = await pump.send_request(R2_SET_POINT_SIGNAL_TYPE_CMD)
    logger.debug(f"R2_SET_POINT_SIGNAL_TYPE_CMD {response.data}")
    # assert bool(response) is False

    response = await pump.send_request(R2_SET_POINT_HYSTERESIS_CMD)
    logger.debug(f"R2_SET_POINT_HYSTERESIS_CMD {response.data}")
    # assert int(response) == 2

    response = await pump.send_request(R2_SET_POINT_PRESSURE_VALUE_CMD)
    logger.debug(f"R2_SET_POINT_THRESHOLD_CMD {response.data}")
    # assert int(response) == 2

    response = await pump.send_request(START_OUTPUT_MODE_CMD)
    logger.debug(f"START_OUTPUT_MODE_CMD {response.data}")
    # assert bool(response) == False

    response = await pump.send_request(GAS_TYPE_CMD)
    logger.debug(f"GAS_TYPE_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(GAS_CORRECTION_CMD)
    logger.debug(f"GAS_CORRECTION_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(PUMP_CURRENT_CMD)
    logger.debug(f"PUMP_CURRENT_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(PUMP_VOLTAGE_CMD)
    logger.debug(f"PUMP_VOLTAGE_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(PUMP_POWER_CMD)
    logger.debug(f"PUMP_POWER_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(DRIVE_FREQUENCY_CMD)
    logger.debug(f"DRIVE_FREQUENCY_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(PUMP_TEMPERATURE_CMD)
    logger.debug(f"PUMP_TEMPERATURE_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(CONTROLLER_HEATSINK_TEMPERATURE_CMD)
    logger.debug(f"CONTROLLER_HEATSINK_TEMPERATURE_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(CONTROLLER_AIR_TEMPERATURE_CMD)
    logger.debug(f"CONTROLLER_AIR_TEMPERATURE_CMD  {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(GAUGE_READ_CMD)
    logger.debug(f"GAUGE_READ_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(ROTATION_FREQUENCY_CMD)
    logger.debug(f"ROTATION_FREQUENCY_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(GAUGE_STATUS_CMD)
    logger.debug(f"GAUGE_STATUS_CMD {response.data}")
    # assert int(response) == 0

    response = await pump.send_request(GAUGE_POWER_CMD)
    logger.debug(f"GAUGE_POWER_CMD {response.data}")
    # assert int(response) == 0


@pytest.mark.asyncio
async def test_high_level(pump):
    pause_time = 0.1

    status = await pump.get_status()
    assert status is PumpStatus.STOP

    error = await pump.get_error()
    assert error is PumpErrorCode.NO_ERROR

    # soft start
    soft_start_backup = await pump.get_soft_start()
    logger.info(f"soft start {soft_start_backup}")
    await pump.set_soft_start(False)
    await asyncio.sleep(pause_time)
    assert await pump.get_soft_start() is False
    await pump.set_soft_start(True)
    await asyncio.sleep(pause_time)
    assert await pump.get_soft_start() is True
    await pump.set_soft_start(soft_start_backup)
    await asyncio.sleep(pause_time)

    # active stop
    active_stop_backup = await pump.get_active_stop()
    logger.info(f"active stop {active_stop_backup}")
    await pump.set_active_stop(False)
    await asyncio.sleep(pause_time)
    assert await pump.get_active_stop() is False
    await pump.set_active_stop(True)
    await asyncio.sleep(pause_time)
    assert await pump.get_active_stop() is True
    await pump.set_active_stop(active_stop_backup)
    await asyncio.sleep(pause_time)

    # external cooling fan
    fan_cfg_backup = await pump.get_fan_config()
    logger.info(f"external fan config {fan_cfg_backup}")
    await pump.set_fan_config(1)  # automatic
    await asyncio.sleep(pause_time)
    assert await pump.get_fan_config() == 1
    await pump.set_fan_config(2)  # serial
    await asyncio.sleep(pause_time)
    assert await pump.get_fan_config() == 2
    await pump.set_fan_config(0)  # ON
    await asyncio.sleep(pause_time)
    assert await pump.get_fan_config() == 0
    await pump.set_fan_config(fan_cfg_backup)

    fan_backup = await pump.get_fan()
    logger.info(f"external fan {fan_backup}")
    await pump.set_fan(True)
    await asyncio.sleep(pause_time)
    assert await pump.get_fan() is True
    await pump.set_fan(False)
    await asyncio.sleep(pause_time)
    assert await pump.get_fan() is False
    await pump.set_fan(fan_backup)

    # Vent valve
    await pump.set_vent_operation(True)
    assert await pump.get_vent_operation() is True

    valve = await pump.get_vent_open()
    logger.info(f"vent valve {valve}")
    await pump.set_vent_open(True)
    await asyncio.sleep(pause_time)
    assert await pump.get_vent_open() is True
    await pump.set_vent_open(False)
    await asyncio.sleep(pause_time)
    assert await pump.get_vent_open() is False

    await pump.set_vent_operation(False)
    assert await pump.get_vent_operation() is False

    open_backup = await pump.get_vent_open_time()
    logger.info(f"vent valve open time {open_backup} s")
    await pump.set_vent_open_time(99.4)
    await asyncio.sleep(pause_time)
    assert await pump.get_vent_open_time() == pytest.approx(99.4)
    await pump.set_vent_open_time(open_backup)
    await asyncio.sleep(pause_time)
    assert await pump.get_vent_open_time() == pytest.approx(open_backup)

    delay_backup = await pump.get_vent_delay_time()
    logger.info(f"vent valve opening delay {delay_backup} s")
    await pump.set_vent_delay_time(100.4)
    await asyncio.sleep(pause_time)
    assert await pump.get_vent_delay_time() == pytest.approx(100.4)
    await pump.set_vent_delay_time(delay_backup)
    await asyncio.sleep(pause_time)
    assert await pump.get_vent_delay_time() == pytest.approx(delay_backup)

    gauge_power_bkp = await pump.get_gauge_power()
    await pump.set_gauge_power(0)  # off
    assert await pump.get_gauge_power() == 0
    await pump.set_gauge_power(1)  # on
    assert await pump.get_gauge_power() == 1
    gauge_status = await pump.get_gauge_status()
    logger.info(f"Gauge power: {gauge_power_bkp} status: {gauge_status.name}")
    await pump.set_gauge_power(gauge_power_bkp)  # off

    # read turbo speed and temperature
    speed = await pump.read_turbo_speed()
    assert isinstance(speed, float)
    temp = await pump.read_turbo_temp()
    assert isinstance(temp, float)
    assert temp > 15.0
    assert temp < 70.0
    logger.info(f"Turbo speed: {speed} rpm, temp: {temp} °C")

    unit = await pump.get_pressure_unit()
    value = await pump.read_pressure()
    logger.info(f"Pressure {value} {unit}")


@pytest.mark.asyncio
async def test_fan_on(pump):
    pause_time = 0.1

    status = await pump.get_status()
    assert status is PumpStatus.STOP
    await pump.set_fan_config(2)  # ON
    await asyncio.sleep(pause_time)
    assert await pump.get_fan_config() == 2
    await pump.set_fan(True)
    assert await pump.get_fan() is True


@pytest.mark.asyncio
async def test_fan_off(pump):
    pause_time = 0.1

    status = await pump.get_status()
    assert status is PumpStatus.STOP
    await pump.set_fan_config(2)  # ON
    await asyncio.sleep(pause_time)
    assert await pump.get_fan_config() == 2
    await pump.set_fan(False)
    assert await pump.get_fan() is False
    await pump.set_fan_config(1)  # AUTO


@pytest.mark.asyncio
async def test_get_R1_config(pump):
    setpoint_config = await pump.get_setpoint(1)
    logger.debug(f"Setpoint config: {setpoint_config}")


@pytest.mark.asyncio
async def test_set_R1_config(pump):
    old_config = await pump.get_setpoint(1)
    logger.debug(f"Setpoint old config: {old_config}")

    await pump.set_setpoint(1, setpoint_tuple=old_config)
    assert await pump.get_setpoint(1) == old_config

    await pump.set_setpoint(1, point_type=SetpointType.FREQ, value=40000)
    config = await pump.get_setpoint(1)
    assert config.point_type == SetpointType.FREQ
    assert config.value == 40000

    # restore
    await pump.set_setpoint(1, setpoint_tuple=old_config)
    assert await pump.get_setpoint(1) == old_config


@pytest.mark.asyncio
async def test_set_R2_config(pump):
    old_config = await pump.get_setpoint(2)
    await pump.set_setpoint(2, setpoint_tuple=old_config)
    assert await pump.get_setpoint(2) == old_config

    await pump.set_setpoint(2, point_type=SetpointType.FREQ, value=40000)
    config = await pump.get_setpoint(2)
    assert config.point_type == SetpointType.FREQ
    assert config.value == 40000

    # restore
    await pump.set_setpoint(2, setpoint_tuple=old_config)
    assert await pump.get_setpoint(2) == old_config
