"""Test pypco module."""

#pylint: disable=unused-import

import unittest

import pypco

class TestExpectedImports(unittest.TestCase):
    """Verify expected classes and functions can be resolved from primary module."""

    def test_main_class_available(self):
        """Verify primary PCO class can be resolved."""

        try:
            from pypco import PCO
        except ImportError as err:
            self.fail(err.msg)

    def test_exception_classes_available(self):
        """Verify exception classes can be resolved."""

        try:
            from pypco import PCOException
            from pypco import PCOCredentialsException
            from pypco import PCORequestTimeoutException
            from pypco import PCOUnexpectedRequestException
            from pypco import PCORequestTimeoutException
        except ImportError as err:
            self.fail(err.msg)

    def test_user_auth_helper_classes_available(self):
        """Verify user auth helper classes can be resolved."""

        try:
            from pypco import get_browser_redirect_url
            from pypco import get_oauth_access_token
            from pypco import get_oauth_refresh_token
        except ImportError as err:
            self.fail(err.msg)
