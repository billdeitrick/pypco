"""Test the primary pypco entry point -- the PCO object"""

from pypco import PCO
from pypco.pco import PCOAuthConfig
import pypco.endpoints as endpoints
from tests import BasePCOVCRTestCase

#pylint: disable=E1101

class TestPCO(BasePCOVCRTestCase):
    """Test the PCO class."""

    def test_auth_config_exist(self):
        """Verify that the auth config object is present on a new PCO object."""

        self.assertIsInstance(PCO(token="test").auth_config, PCOAuthConfig)

    def test_endpoint_init(self):
        """Verify that endpoints are initialized successfully"""

        pco = PCO(token="test")

        self.assertIsInstance(pco.people, endpoints.people.PeopleEndpoint)
