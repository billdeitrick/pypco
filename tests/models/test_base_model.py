"""Tests for the base model class."""

#pylint: disable=E1101

import pypco
from .. import BasePCOVCRTestCase

# TODO: Figure out why pyvcr isn't working

class TestModels(BasePCOVCRTestCase):
    """Test the BaseModel class."""

    def setUp(self): #pylint: disable=C0103
        """Configure test objects for models."""

        self.pco = pypco.PCO(self.creds['application_id'], self.creds['secret']) #pylint: disable=W0201

    def test_properties_exist(self):
        """Verify the correct properties exist on the BaseModel object."""

        test_person = self.pco.people.people.get("16555904")

        self.assertIsInstance(test_person, pypco.models.people.Person)

        self.assertIsInstance(test_person._endpoint, pypco.endpoints.people.People) #pylint: disable=W0212
        self.assertIsInstance(test_person._data, dict) #pylint: disable=W0212
        self.assertFalse(test_person._user_created) #pylint: disable=W0212
        self.assertTrue(test_person._from_get) #pylint: disable=W0212