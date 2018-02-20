"""Test the primary pypco entry point -- the PCO object"""

from pypco import PCO
from pypco.pco import PCOAuthConfig
import pypco.endpoints as endpoints
import pypco.models as models
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

    def test_basic_crud_function(self):
        """Test basic CRUD functionality of the API."""

        pco = self.pco

        # Test a simple get request
        result = pco.people.people.get("16555904")
        self.assertIsInstance(result, models.people.Person)
        self.assertEqual(result.first_name, 'Paul')
        self.assertEqual(result.last_name, 'Revere')

        # Test a simple get request with multiple results
        results = pco.people.people.list(where={'last_name': 'Revere'})
        for result in results:
            self.assertIsInstance(result, models.people.Person)
            self.assertEqual(result.last_name, 'Revere')

        # TODO: Test updating an object
        # TODO: Test creating an object
        # TODO: Test deleting an object
