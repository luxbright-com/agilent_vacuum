from .communication import Command, DataType

"""
Common commands. Response protocol might depend on device model
"""

BAUD_RATE_CMD = Command(win=108, writable=True, datatype=DataType.NUMERIC, description="Baud rate")
STATUS_CMD = Command(win=205, writable=False, datatype=DataType.NUMERIC, description='Status')
ERROR_CODE_CMD = Command(win=206, writable=False, datatype=DataType.NUMERIC, description="Error code")
ADDR_CMD = Command(win=503, writable=True, datatype=DataType.NUMERIC, description="RS485 Serial Address [0-31] 1=def")
SERIAL_ADDR_CMD = Command(win=503, writable=True, datatype=DataType.NUMERIC,
                          description="RS485 Serial Address [0-31]; 1=def")
SERIAL_TYPE_CMD = Command(win=504, writable=True, datatype=DataType.LOGIC,
                          description="Serial Type Select 0= RS232(def) 1= RS485")
