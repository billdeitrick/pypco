"""All pypco exceptions."""

class PCOException(Exception):
    """A base class for all pypco exceptions."""

class PCOCredentialsException(PCOException):
    """Unusable credentials are supplied to pypco."""

class PCORequestTimeoutException(PCOException):
    """Request to PCO timed out after the maximum number of retries."""

class PCORequestException(PCOException):
    """The response from the PCO API indicated an error with your request.

    Args:
        status_code (int): The HTTP status code corresponding to the error.
        message (str): The error message string.
    """

    def __init__(self, status_code, message): #pylint: disable=super-init-not-called
        self.status_code = status_code
        self.message = message
