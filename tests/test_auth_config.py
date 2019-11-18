"""Test the PCO auth configuration module."""

from pypco.auth_config import PCOAuthConfig, PCOAuthType
from pypco.exceptions import PCOCredentialsException
from tests import BasePCOTestCase

class TestPCOAuthConfig(BasePCOTestCase):
    """Test the PCOAuthConfig class."""

    def test_pat(self):
        """Verify class functionality with personal access token."""

        auth_config = PCOAuthConfig('app_id', 'secret')

        self.assertIsInstance(auth_config, PCOAuthConfig, "Class is not instnace of PCOAuthConfig!")

        self.assertIsNotNone(auth_config.application_id, "No application_id found on object!")
        self.assertIsNotNone(auth_config.secret, "No secret found on object!")

        self.assertEqual(auth_config.auth_type, PCOAuthType.PAT, "Wrong authentication type!")

    def test_oauth(self):
        """Verify class functionality with OAuth."""

        auth_config = PCOAuthConfig(token="abcd1234")

        self.assertIsInstance(auth_config, PCOAuthConfig, "Class is not instnace of PCOAuthConfig!")

        self.assertIsNotNone(auth_config.token, "No token found on object!")

        self.assertEqual(auth_config.auth_type, PCOAuthType.OAUTH, "Wrong authentication type!")

    def test_invalid_auth(self):
        """Verify an error when we try to get auth type with bad auth."""

        # Test with only auth_id
        with self.assertRaises(PCOCredentialsException):
            PCOAuthConfig('bad_app_id').auth_type #pylint: disable=W0106

        # Test with only secret
        with self.assertRaises(PCOCredentialsException):
            PCOAuthConfig(secret='bad_app_secret').auth_type #pylint: disable=W0106

        # Test with token and auth_id
        with self.assertRaises(PCOCredentialsException):
            PCOAuthConfig(application_id='bad_app_id', token='token').auth_type #pylint: disable=W0106

        # Test with token and secret
        with self.assertRaises(PCOCredentialsException):
            PCOAuthConfig(secret='bad_secret', token='bad_token').auth_type #pylint: disable=W0106

        # Test with no args
        with self.assertRaises(PCOCredentialsException):
            PCOAuthConfig().auth_type #pylint: disable=W0106

    def test_auth_headers(self):
        """Verify that we get the correct authentication headers."""

        # PAT
        auth_config = PCOAuthConfig('app_id', 'secret')
        self.assertEqual(auth_config.auth_header, "Basic YXBwX2lkOnNlY3JldA==", \
            "Invalid PAT authentication header.")

        # OAUTH
        auth_config = PCOAuthConfig(token="abcd1234")
        self.assertEqual(auth_config.auth_header, "Bearer abcd1234", \
            "Invalid OAUTH authentication header.")
