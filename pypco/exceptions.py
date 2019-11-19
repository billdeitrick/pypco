"""All pypco exceptions."""

class PCOException(Exception):
    """A base class for all pypco exceptions."""

class PCOCredentialsException(PCOException):
    """Unusable credentials are supplied to pypco."""

class PCORequestTimeoutException(PCOException):
    """Request to PCO timed out after the maximum number of retries."""
