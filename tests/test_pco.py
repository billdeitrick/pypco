"""Test the primary pypco entry point -- the PCO object"""

from pypco import PCO
from pypco.pco import PCOAuthConfig
import pypco.endpoints as endpoints
import pypco.models as models
import pypco
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

        # TODO: Add high-level tests to ensure user interface stability

    def test_new(self):
        """Test the new function (a factory function to create new PCO API objects)"""

        pco = self.pco

        # Try a test person
        new_person = pco.new(pypco.models.people.Person)

        # Verify our new person is an instance of the correct object and 
        # that they are in the correct state.
        self.assertIsInstance(new_person, pypco.models.people.Person)
        self.assertIs(new_person._endpoint, pco.people.people)
        self.assertEqual(new_person.type, "Person")
        self.assertEqual(new_person.attributes, {})
        self.assertEqual(new_person._update_attribs, set())
        self.assertEqual(new_person._update_relationships, set())
        self.assertEqual(new_person._user_created, True)
        self.assertEqual(new_person._from_get, False)

        # Try a test person address
        new_address = pco.new(pypco.models.people.Address)

        # Verify our new person is an instance of the correct object and 
        # that they are in the correct state.
        self.assertIsInstance(new_address, pypco.models.people.Address)
        self.assertIs(new_address._endpoint, pco.people.addresses)
        self.assertEqual(new_address.type, "Address")
        self.assertEqual(new_address.attributes, {})
        self.assertEqual(new_address._update_attribs, set())
        self.assertEqual(new_person._update_relationships, set())
        self.assertEqual(new_address._user_created, True)
        self.assertEqual(new_address._from_get, False)
