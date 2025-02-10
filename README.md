# Agilent-Vacuum
A collection of classes for communication with various Agilent Vacuum pump controllers.

This package supports:
* Agilent TwissTorr 74FS Rack Turbo Pump controller [PDF user guide](https://www.agilent.com/cs/library/usermanuals/public/TwisTorr%2074%20FS%20AG%20Rack%20Controller.pdf)
* Agilent IPCMini Ion Pump Controller [PDF user guide](https://www.agilent.com/cs/library/usermanuals/public/IPCMini.pdf)

This is was developed for internal use at Luxbright.
It has been used 24/7 in production lines and R&D labs since year 2023.
But we only use a subset of all implemented commands and not all commands are tested by the pytest suite.

I hope that it can be useful as it is, or as source of inspiration for somebudy else.
This is not an official library from Agilent and we are not associated with the, 
we are only a user of their products.

This library is implemented using asyncio.

## Turbo pump driver usage

    from agilent_vacuum.twis_torr_74 import TwisTorr74Driver
    from agilent_vacuum.communication import PressureUnit, SerialClient
    from agilent_vacuum.exceptions import ComError, WinDisabled
 

Create a serial client, this exaple connects to a USB to RS232 adapter on a Raspberry Pi.
Initiate a driver and try to connect to controller.

    client = SerialClient("/dev/ttyS0")
    turbo = TwisTorr74Driver(client)
    try:
        await turbo.connect()
    except ComError as e:
        logger.warning(f"Turbo pump connect failed. {e}")
    except EOFError as e:
        logger.warning(f"Turbo pump connect failed. {e}")

Start turbo pump and read status and speed.

    await turbo.start()
    status = await turbo.get_status()
    speed = await turbo.read_turbo_speed
    logger.info(f"Turbo status {status.name} and speed {speed} rpm.")

Read vacuum gauge (requires optional gauge connected to controller)

    unit = await turbo.get_pressure_unit()
    value = await turbo.read_presure()
    logger.info(f"{pressure} {unit.name}")

Stop turbo pump.

    await turbo.stop()


## Ion pump driver usage

    from agilent_vacuum.ipc_mini import IpcMiniDriver, PumpStatus
    from agilent_vacuum.communication import PressureUnit, SerialClient
    from agilent_vacuum.exceptions import ComError, WinDisabled

Create a serial client, this exaple connects to the UART on a Raspberry Pi via an RS323 circuit.
Initiate a driver and try to connect to controller.

    client = SerialClient("/dev/ttyS0")
    ion_pump = IpcMiniDriver(client)
    try:
        await ion_pump.connect()
    except ComError as e:
        logger.warning(f"Turbo pump connect failed. {e}")
    except EOFError as e:
        logger.warning(f"Turbo pump connect failed. {e}")

Start the Ion Pump and read status

    await ion_pump.start()
    status = await ion_pump.get_status()
    logger.info(f"Ion pump status {status.name}")

Read vacuum level

    unit = await ion_pump.get_pressure_unit()
    value = await ion_pump.read_presure()
    logger.info(f"{pressure} {unit.name}")

Stop Ion Pump

    await ion_pump.stop()

