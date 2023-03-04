"""
A Pythonic Object-Oriented wrapper to the PCO API

pypco is a Python wrapper for the Planning Center Online (PCO) REST API
intended to help you accomplish useful things with Python and the PCO API
more quickly. pypco provides simple helpers wrapping the REST calls you'll
place against the PCO API, meaning that you'll be spending your time
directly in the PCO API docs rather than those specific to your API wrapper
tool of choice.

usage:
    >>> import pypco
    >>> pco = pypco.PCO()

pypco supports both OAUTH and Personal Access Token (PAT) authentication.
"""

# PyPCO Version
__version__ = "1.2.0"

# Export the interface we present to clients

# The primary PCO interface object
from .pco import PCO

# Utility functions for OAUTH
from .user_auth_helpers import *

# Import exceptions
from .exceptions import *
