"""
Exceptions matching errors defined in Agilent documentation
"""


class NACK(Exception):
    """
    Execution of the command has failed.
    """


class UnknownWindow(Exception):
    """
    The window specified in the command is not a valid window.
    """


class DataTypeError(TypeError):
    """
    The data type specified in the command (Logic, Numeric or Alphanumeric) is not in agreement with
    the Window specified.
    """


class OutOfRange(ValueError):
    """
    The value expressed during a write command is not within the range value for the specified window.
    """


class WinDisabled(Exception):
    """
    The window specified is Read Only or is temporarily disabled.
    """


class ComError(Exception):
    """
    The pump controller does not respond, or some other communication error occurred.
    """
