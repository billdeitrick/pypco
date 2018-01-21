"""Test endpoint utility classes"""

from pypco.endpoints.utils import PCOAuthConfig, PCOAuthException, PCOAuthType
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
        with self.assertRaises(PCOAuthException):
            PCOAuthConfig('bad_app_id').auth_type #pylint: disable=W0106

        # Test with only secret
        with self.assertRaises(PCOAuthException):
            PCOAuthConfig(secret='bad_app_secret').auth_type #pylint: disable=W0106

        # Test with token and auth_id
        with self.assertRaises(PCOAuthException):
            PCOAuthConfig(application_id='bad_app_id', token='token').auth_type #pylint: disable=W0106

        # Test with token and secret
        with self.assertRaises(PCOAuthException):
            PCOAuthConfig(secret='bad_secret', token='bad_token').auth_type #pylint: disable=W0106

        # Test with no args
        with self.assertRaises(PCOAuthException):
            PCOAuthConfig().auth_type #pylint: disable=W0106