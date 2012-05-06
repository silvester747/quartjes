"""
Exceptions used as part of the connector.
"""

__author__ = "Rob van der Most"
__docformat__ = "restructuredtext en"

class ProtocolError(Exception):
    """
    Base class for all protocol related exceptions.
    """

class MessageHandleError(ProtocolError):
    """
    Exception thrown by the server when handling an incoming message has failed.
    This exception is recreated by the client if no appropriate builtin exception
    can be thrown.
    
    error_code : int
        An error code stating what went wrong handling the message. Should be one of the
        codes in this class.
    original_message : quartjes.connector.messages.Message
        The original message that could not be handled.
    error_details : string
        Detailed description of the error that occurred.

    """

    RESULT_OK = 0
    """
    No error occured. 
    """
    
    RESULT_XML_PARSE_FAILED = 1
    """
    Parsing the XML in the message failed.
    """
    
    RESULT_XML_INVALID = 2
    """
    The XML does not contain valid content.
    """
    
    RESULT_UNKNOWN_MESSAGE = 3
    """
    The message type is unknown.
    """
    
    RESULT_UNEXPECTED_MESSAGE = 4
    """
    In the current state the connector does not accept the message.
    """
    
    RESULT_UNKNOWN_SERVICE = 5
    """
    The service is not registered to the connector.
    """
    
    RESULT_UNKNOWN_METHOD = 6
    """
    The method is not present or not remote accessible.
    """
    
    RESULT_INVALID_PARAMS = 7
    """
    The parameters do not match the method signature.
    """
    
    RESULT_EXCEPTION_RAISED = 8
    """
    An exception was encountered while processing the request.
    """
    
    RESULT_UNKNOWN_EVENT = 9
    """
    The event is not present or not remote accessible.
    """
    
    RESULT_UNKNOWN_ERROR = 99
    """
    An unexpected error has occurred.
    """

    def __init__(self, error_code=RESULT_UNKNOWN_ERROR, original_message=None, error_details=None):
        self.error_code = error_code
        self.original_message = original_message
        self.error_details = error_details

    def __str__(self):
        return "MessageHandleError: (%d) %s" % (self.error_code, self.error_details)

class ConnectionError(ProtocolError):
    """
    Exception thrown when an error occurs in the connection.
    
    message : string
        Message describing the error.
    """

    def __init__(self, message=None):
        self.message = message

class TimeoutError(ProtocolError):
    """
    Exception thrown when an action on the server times out.
    
    message : string
        Message describing the error.
    """
    def __init__(self, message=None):
        self.message = message

