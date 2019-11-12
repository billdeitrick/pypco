"""All pypco exceptions."""

class PCOException(Exception):
    """A base class for all pypco exceptions."""

class PCOCredentialsException(PCOException):
    """Thrown when unusable credentials are supplied to pypco."""
