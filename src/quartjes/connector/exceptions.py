"""
Exceptions used as part of the connector.
"""

__author__="rob"
__date__ ="$Aug 21, 2011 8:28:19 PM$"

class ProtocolError(Exception):
    """
    Base class for all protocol related exceptions.
    """

class MessageHandleError(ProtocolError):
    """
    Exception thrown by the server when handling an incoming message has failed.
    This exception is recreated by the client if no appropriate builtin exception
    can be thrown.
    """

    RESULT_OK = 0
    RESULT_XML_PARSE_FAILED = 1
    RESULT_XML_INVALID = 2
    RESULT_UNKNOWN_MESSAGE = 3
    RESULT_UNEXPECTED_MESSAGE = 4
    RESULT_UNKNOWN_SERVICE = 5
    RESULT_UNKNOWN_ACTION = 6
    RESULT_INVALID_PARAMS = 7
    RESULT_EXCEPTION_RAISED = 8
    RESULT_UNKNOWN_ERROR = 99

    def __init__(self, error_code=RESULT_UNKNOWN_ERROR, original_message=None, error_details=None):
        self.error_code = error_code
        self.original_message = original_message
        self.error_details = error_details

    def __str__(self):
        return "MessageHandleError: (%d) %s" % (self.error_code, self.error_details)

class ConnectionError(ProtocolError):
    """
    Exception thrown when an error occurs in the connection.
    """

    def __init__(self, message=None):
        self.message = message

class TimeoutError(ProtocolError):
    """
    Exception thrown when an action on the server times out.
    """
    def __init__(self, message=None):
        self.message = message

