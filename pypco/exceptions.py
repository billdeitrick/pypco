"""All pypco exceptions."""

class PCOException(Exception):
    """A base class for all pypco exceptions."""

class PCOCredentialsException(PCOException):
    """Unusable credentials are supplied to pypco."""

class PCORequestTimeoutException(PCOException):
    """Request to PCO timed out after the maximum number of retries."""

class PCOUnexpectedRequestException(PCOException):
    """An unexpected exception has occurred attempting to make the request.

    We don't have any additional information associated with this exception.
    """

class PCORequestException(PCOException):
    """The response from the PCO API indicated an error with your request.

    Args:
        status_code (int): The HTTP status code corresponding to the error.
        message (str): The error message string.
        response_body (str): The body of the response (may include helpful information).
            Defaults to None.

    Attributes:
        status_code (int): The HTTP status code returned.
        message (str): The error message string.
        response_body (str): Text included in the response body. Often
            includes additional informative errors describing the problem
            encountered.
    """

    def __init__(self, status_code, message, response_body=None): #pylint: disable=super-init-not-called
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
