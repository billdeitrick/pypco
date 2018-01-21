"""Unit tests for pypco"""

import os
import logging
import logging.handlers
import unittest
import vcr_unittest

PYCO_LOGGER_EXISTS = False

def get_creds_from_environment():
    """Gets authentication credentials from environment.

    If they don't exist, raises an error.

    We expect the following token elements to be present as environment variables:
    PCO_APP_ID
    PCO_SECRET

    Returns:
        Dict: Personal access token for connecting to PCO {application_id: ..., secret: ...}

    Raises:
        VarsNotFoundError
    """

    try:
        creds = {}

        creds['application_id'] = os.environ['PCO_APP_ID']
        creds['secret'] = os.environ['PCO_SECRET']

    except KeyError:
        raise CredsNotFoundError("PCO_APP_ID and/or PCO_SECRET environment variables not found.")

    return creds

def build_logging_environment():
    """Builds logging for the environment.

    If the necessary environment variables don't exist, skip logging.
    We look for the following vars:
    PYPCO_LOG_DIR (the directory in which logs should be stored)
    """

    global PYCO_LOGGER_EXISTS #pylint: disable=W0603

    try:
        if not PYCO_LOGGER_EXISTS:
            log_dir = os.environ['PYPCO_LOG_DIR']

            # Build logger
            log = logging.getLogger('pypco')
            log.setLevel(logging.DEBUG)

            # Build file handler
            file_handler = logging.handlers.RotatingFileHandler(
                "{}{}{}".format(log_dir, os.sep, "pypco.log"),
                maxBytes=50000,
                backupCount=10
            )
            file_handler.setLevel(logging.DEBUG)

            # Build formatter
            formatter = logging.Formatter(
                '%(levelname)8s  %(asctime)s  [%(module)s|%(lineno)d]  %(message)s'
            )
            file_handler.setFormatter(formatter)

            # Add file handler to logger
            log.addHandler(file_handler)

            PYCO_LOGGER_EXISTS = True

    except KeyError:
        pass

class CredsNotFoundError(Exception):
    """Exception indicating environment variables not found."""
    pass

class BasePCOTestCase(unittest.TestCase):
    """"A base class for unit tests on pypco library.

    This class provides boilerplate for pulling authentication and
    logging configuration.

    Attributes:
        creds (dict): PCO personal tokens for executing test requests.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the test case."""

        unittest.TestCase.__init__(self, *args, **kwargs)

        build_logging_environment()

class BasePCOVCRTestCase(vcr_unittest.VCRTestCase):
    """"A base class for unit tests on pypco with the VCR library.

    This class provides boilerplate for pulling authentication and
    logging configuration.

    Attributes:
        creds (dict): PCO personal tokens for executing test requests.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the test case."""

        vcr_unittest.VCRTestCase.__init__(self, *args, **kwargs)

        self.creds = get_creds_from_environment()
        build_logging_environment()
