"""Tests for the base model class."""

#pylint: disable=E1101

import unittest
from requests import HTTPError
from .. import BasePCOVCRTestCase
import pypco

class TestModels(BasePCOVCRTestCase):
    """Test the BaseModel class."""

    def test_basic_get(self):
        """Verify that we can instantiate from get request and basic properties exist."""

        test_person = self.pco.people.people.get("16555904")

        # Verify we got a Person object
        self.assertIsInstance(test_person, pypco.models.people.Person)

        # Verify the Person object has the correct endpoint set
        self.assertIsInstance(test_person._endpoint, pypco.endpoints.people.People) #pylint: disable=W0212

        # Verify the Person object has the data dict set
        self.assertIsInstance(test_person._data, dict) #pylint: disable=W0212

        # Verify the object was not a new object created by the user
        self.assertFalse(test_person._user_created) #pylint: disable=W0212

        # Verify the object was created from a direct get request
        self.assertTrue(test_person._from_get) #pylint: disable=W0212

    def test_get_dynamic_attribs_basic(self):
        """Verify that we can get basic dynamic attributes from model (relying on model's __getattr__)"""

        test_person = self.pco.people.people.get("16555904")

        # Verify we got a person object
        self.assertIsInstance(test_person, pypco.models.people.Person)

        # Check that the expected attribs are available
        self.assertEqual(test_person.type, "Person")
        self.assertEqual(test_person.id, "16555904")
        self.assertEqual(test_person.first_name, "Paul")
        self.assertEqual(test_person.last_name, "Revere")
        self.assertEqual(test_person.birthdate, "1916-01-01")
        self.assertEqual(test_person.middle_name, None)

        # Verify we get an AttributeError on an attribute that isn't available
        with self.assertRaises(AttributeError):
            attrib = test_person.bogus_attrib #pylint: disable=W0612

    def test_set_dynamic_attribs_basic(self):
        """Verify that we can set dynamic attributes on model (relying on model's __setattr__)"""

        test_person = self.pco.people.people.get("16555904")

        # Set the person's name, and ensure it was changed
        test_person.first_name = "George"
        self.assertEqual(test_person.first_name, "George")

        # Set the person's birthdate and ensure it was changed
        test_person.birthdate = "1950-1-1"
        self.assertEqual(test_person.birthdate, "1950-1-1")

    def test_delete(self):
        """Test deleting an object from PCO."""

        pco = self.pco

        # Verify we can retrieve and delete an object

        # Get our victim
        person = pco.people.people.get("34762810")

        # Verify who we wanted
        self.assertIsInstance(person, pypco.models.people.Person)
        self.assertEqual(person.first_name, 'Pico')
        self.assertEqual(person.last_name, 'Robot')

        # Bye bye, Pico
        person.delete()

        # Verify Pico is gone...sniff.
        with self.assertRaises(HTTPError):
            pco.people.people.get("34762810")

        # Verify exception is thrown when we attempt to delete a user
        # via an object never synced with PCO
        bad_person = pypco.models.people.Person(None)

        with self.assertRaises(pypco.models.base_model.PCOModelStateError):
            bad_person.delete()

    def test_update(self):
        """Test updating an object in PCO."""

        pco = self.pco

        # Get our test victim, verify attributes are as expected
        pico = pco.people.people.get("34765191")
        self.assertEqual(pico.child, False)
        self.assertEqual(pico.nickname, None)
        
        # Change our test victim, ensure attributes are saved
        pico.child = True
        pico.nickname = "PiRo"
        self.assertEqual(pico.child, True)
        self.assertEqual(pico.nickname, "PiRo")

        # Update our test victim, ensure attributes come back
        pico.update()
        self.assertEqual(pico.child, True)
        self.assertEqual(pico.nickname, "PiRo")

        # Get another instance of our test victim, verify correct attributes
        pico2 = pco.people.people.get("34765191")
        self.assertEqual(pico.child, True)
        self.assertEqual(pico.nickname, "PiRo")

        # Set our test victime back, and verify correct attributes
        pico2.child = False
        pico2.nickname = None
        pico2.update()

        self.assertEqual(pico2.child, False)
        self.assertEqual(pico2.nickname, None)

        # Test more updates using same object
        # This verifies changed attribute tracking is reset properly
        pico2.child = True
        pico2.nickname = "PiRo"
        pico2.update()

        self.assertEqual(pico2.child, True)
        self.assertEqual(pico2.nickname, "PiRo")

        # Verify attributes were set properly with a third object
        # Reset the original object
        pico3 = pco.people.people.get("34765191")
        
        self.assertEqual(pico3.child, True)
        self.assertEqual(pico3.nickname, "PiRo")

        pico3.child = False
        pico3.nickname = None
        pico3.update()

    def test_get_updates(self):
        """Test serializing an object's updates to be sent to PCO."""

        pco = self.pco

        pico = pco.people.people.get("34765191")
        self.assertIsInstance(pico, pypco.models.people.Person)
        self.assertEqual(pico.child, False)
        self.assertEqual(pico.middle_name, None)
        self.assertEqual(pico.nickname, None)

        pico.child = True
        pico.middle_name = 'Cool'
        pico.nickname = 'PiRo'

        expected_dict = {
            'data': {
                'type': 'Person',
                'id': '34765191',
                'attributes': {
                    'child': True,
                    'middle_name': 'Cool',
                    'nickname': 'PiRo'
                }
            }
        }

        actual_dict = pico._get_updates()

        self.assertEqual(expected_dict, actual_dict)
