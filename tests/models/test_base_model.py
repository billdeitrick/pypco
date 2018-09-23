"""Tests for the base model class."""

#pylint: disable=E1101

import unittest
from requests import HTTPError
from .. import BasePCOVCRTestCase
from .. import BasePCOTestCase
from pypco.models.base_model import * #pylint: disable=W0614
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

        # Verify the data property is available
        self.assertIsInstance(test_person.data, dict)

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

    def test_serialize_updates(self):
        """Test serializing an object's updates to be sent to PCO."""

        pco = self.pco

        # A simple example; no relationships
        #region
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

        actual_dict = pico._serialize_updates()

        self.assertEqual(expected_dict, actual_dict)
        #endregion

        # More complex example involving a relationship
        #region
        email = pco.people.emails.get("12084502")

        self.assertIsInstance(email, pypco.models.people.Email)
        self.assertEqual(email.address, "paul@notarealaddress.com")

        george = pco.people.people.get("23232372")

        self.assertEqual(george.first_name, "George")
        self.assertEqual(george.last_name, "Washington")

        email.rel.person.set(george)
        email.address = "george@nowhere.com"

        expected_dict = {
            'data': {
                'type': 'Email',
                'id': '12084502',
                'attributes': {
                    'address': 'george@nowhere.com'
                },
                'relationships': {
                    'person': {
                        'data': {
                            'type': 'Person',
                            'id': '23232372'
                        }
                    }
                }
            }
        }

        actual_dict = email._serialize_updates()

        self.assertEqual(expected_dict, actual_dict)

        #endregion

    def test_refresh(self):
        """Test refreshing the model with data from PCO."""

        pco = self.pco

        # Test soft refreshes without any changes
        # This means there's no user-changed data to avoid overwriting
        #region
        # Get two copies of the same person
        pico1 = pco.people.people.get("34765191")
        pico2 = pco.people.people.get("34765191")

        # Verify expected attrib values
        self.assertEqual(pico1.child, False)
        self.assertEqual(pico1.nickname, None)
        self.assertEqual(pico2.child, False)
        self.assertEqual(pico2.nickname, None)

        # Set attribs on pico1
        pico1.child = True
        pico1.nickname = "PiRo"
        pico1.update()

        # Verify correct attribs, pico2 is same as before
        self.assertEqual(pico1.child, True)
        self.assertEqual(pico1.nickname, "PiRo")
        self.assertEqual(pico2.child, False)
        self.assertEqual(pico2.nickname, None)

        # Refresh pico2, and verify we have correct values
        pico2.refresh()

        self.assertEqual(pico2.child, True)
        self.assertEqual(pico2.nickname, "PiRo")

        # Set values back to previous
        pico1.child = False
        pico1.nickname = None
        pico1.update()
        #endregion

        # Test test hard and soft refreshes with changed data
        # This means there is user-changed data to avoid overwriting
        #region

        pico = pco.people.people.get("34765191")

        pico.first_name = "Pablo"
        pico.last_name = "Robo"

        name_suffix = pco.people.name_suffixes.get("1764420")
        pico.rel.name_suffix.set(name_suffix)

        pico.refresh()

        self.assertEqual(pico.first_name, "Pablo")
        self.assertEqual(pico.last_name, "Robo")

        pico_name_suffix = pico.rel.name_suffix.get()
        self.assertEqual(pico_name_suffix.id, name_suffix.id)

        pico.refresh(hard=True)

        self.assertEqual(pico.first_name, "Pico")
        self.assertEqual(pico.last_name, "Robot")
        with self.assertRaises(PCORelationDoesNotExistError):
            pico.rel.name_suffix.get()
        #endregion

        # Ensure we raise an error if refresh is called on an object
        # That wasn't synced with PCO
        #region
        with self.assertRaises(PCOInvalidModelError):
            pco.new(pypco.models.people.Person).refresh()
        #endregion

    def test_data(self):
        """Test the data property; ensure we get a copy of the data structure."""

        pco = self.pco

        # Get our test victim, ensure expected values are present
        pico1 = pco.people.people.get("34765191")

        self.assertEqual(pico1.last_name, "Robot")

        # Change an attribute in the datastructure copy we got back
        data = pico1.data
        data['attributes']['last_name'] = 'Human'

        # Ensure we didn't change the original object
        self.assertEqual(pico1.last_name, 'Robot')

    def test_str_repr(self):
        """Test the __str__ and __repr__ functions on the base model object."""

        pco = self.pco

        pico = pco.people.people.get("34765191")

        self.assertEqual(str(pico), str(pico._data))
        self.assertEqual(repr(pico), str(pico._data))
    
    def test_create(self):
        """Test creating new simple objects in PCO."""

        pco = self.pco

        new_person = pco.new(pypco.models.people.Person)

        new_person.first_name = "Nathan"
        new_person.last_name = "Hale"

        self.assertTrue(new_person._user_created)
        self.assertFalse(new_person._from_get)

        new_person.create()

        self.assertIn('id', new_person._data)
        self.assertFalse(new_person._user_created)
        self.assertTrue(new_person._from_get)

        with self.assertRaises(PCOModelStateError):
            new_person.create()

        search_results = pco.people.people.list(where={'first_name': 'Nathan', 'last_name': 'Hale'})
        retrieved_person = next(search_results)

        self.assertEqual(new_person.first_name, retrieved_person.first_name)
        self.assertEqual(new_person.last_name, retrieved_person.last_name)
        self.assertEqual(new_person.id, retrieved_person.id)

        with self.assertRaises(PCOModelStateError):
            retrieved_person.create()

        retrieved_person.delete()
    
    def test_relation_wrapper_init(self):
        """Ensure a model's relationship manager object is initialized as expected."""

        pco = self.pco

        person = pco.people.people.get("16555904")

        self.assertIsInstance(person.rel, RelationWrapper)

    def test_relationship_get(self):
        """Test getting a to-one relationship via the model's RelationWrapper."""

        pco = self.pco

        # Test getting a relation from links (after a get request)
        #region
        george = pco.people.people.get("23232372")
        george_suffix = george.rel.name_suffix.get()

        self.assertIsInstance(george_suffix, pypco.models.people.NameSuffix)

        suffix = pco.people.name_suffixes.get("1764422")

        self.assertEqual(george_suffix.id, suffix.id)
        #endregion

        # Test getting a relation from links (after a list request)
        #region
        george = [person for person in pco.people.people.list(where={'id': '23232372'})][0]
        george_suffix = george.rel.name_suffix.get()

        self.assertIsInstance(george_suffix, pypco.models.people.NameSuffix)

        suffix = pco.people.name_suffixes.get("1764422")

        self.assertEqual(george_suffix.id, suffix.id)
        #endregion 

        # Test getting a relation from the relations attrib
        #region

        # We'll use an address object for this, since the associated person
        # is not included as a link
        address = pco.people.addresses.get("28330374")

        paul = address.rel.person.get()
        self.assertIsInstance(paul, pypco.models.people.Person)
        self.assertEqual(paul.id, "16555904")
        #endregion

        # Test getting an empty relation from links
        #region
        george = pco.people.people.get("23232372")
        george_prefix = george.rel.name_prefix.get()

        self.assertIsNone(george_prefix)
        #endregion

        # Test getting an empty relation from relations
        #region
        address = pco.people.addresses.get("28330374")

        address._data['relationships']['person']['data'] = None

        person = address.rel.person.get()

        self.assertIsNone(person)

        #endregion

        # Test getting a non-existent relation
        #region
        with self.assertRaises(PCORelationDoesNotExistError):
            address = pco.people.addresses.get("28330374")
            address.rel.bogus.get()
        #endregion

        # Test getting a relationship from an object with changed relationships
        # We should pull from the relationship attribute rather than links, since
        # Links won't be updated if the object hasn't been saved
        #region
        pico = pco.people.people.get("34765191")

        name_suffix = pco.people.name_suffixes.get("1764420")
        pico.rel.name_suffix.set(name_suffix)

        pico_name_suffix = pico.rel.name_suffix.get()
        self.assertEqual(pico_name_suffix.id, name_suffix.id)
        #endregion

    def test_relationship_list(self):
        """Test getting a to-many relationship via the model's RelationManger."""

        pco = self.pco

        # Multiple tests use these to verify household membership
        household_ids = [
            '23232372',
            '23232378',
            '23232436'
        ]

        # Test getting a relation from links (after a get request)
        #region
        household = pco.people.households.get("2739849")

        count = 0

        for person in household.rel.people.list():
            count += 1
            self.assertIsInstance(person, pypco.models.people.Person)
            self.assertIn(person.id, household_ids)

        self.assertEqual(count, 3)
        #endregion

        # Test getting a relation from links (after a list request)
        #region
        household = [household for households in pco.people.households.list(where={'primary_contact_name': 'George Washington Sr.'})][0]

        count = 0

        for person in household.rel.people.list():
            count += 1
            self.assertIsInstance(person, pypco.models.people.Person)
            self.assertIn(person.id, household_ids)

        self.assertEqual(count, 3)
        #endregion

        # Test getting a relation from the relations attrib
        #region

        # Make a request including the include parameter, since there aren't
        # any endpoints that provide to-many relationships by default in the
        # people API at the present time
        hh_data = pco.people.households.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/households/2739849",
            params = {
                "include": "people"
            }
        )['data']

        household = pypco.models.people.Household(
            pco.people.households,
            hh_data,
            from_get=True
        )

        # Force list() to use the relationships record instead of links
        del household._data['links']['people']

        count = 0

        for person in household.rel.people.list():
            count += 1
            self.assertIsInstance(person, pypco.models.people.Person)
            self.assertIn(person.id, household_ids)

        self.assertEqual(count, 3)
        #endregion

        # Test getting an empty relation from links
        #region
        george = pco.people.people.get("23232372")
        socials = [profile for profile in george.rel.social_profiles.list()]

        self.assertEqual(len(socials), 0)
        #endregion

        # Test getting an empty relation from relations
        #region

        # Make a request including the include parameter, since there aren't
        # any endpoints that provide to-many relationships by default in the
        # people API at the present time
        person_data = pco.people.people.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/23232372",
            params = {
                "include": "social_profiles"
            }
        )['data']

        person = pypco.models.people.Person(
            pco.people.people,
            person_data,
            from_get=True
        )

        # Force list() to use the relationships record instead of links
        del person._data['links']['social_profiles']

        socials = [profile for profile in person.rel.social_profiles.list()]

        self.assertEqual(len(socials), 0)
        #endregion

        # Test getting a non-existent relation
        #region
        with self.assertRaises(PCORelationDoesNotExistError):
            household = pco.people.households.get("2739849")
            results = household.rel.bogus.list()
            next(results)
        #endregion

    def test_relationship_set(self):
        """Test setting the object in a relationship in a to-one relationship."""

        pco = self.pco

        person = pco.people.people.get("23232372")
        suffix = pco.people.name_suffixes.get("1764422")

        person.rel.name_suffix.set(suffix)

        self.assertIn('name_suffix', person.data['relationships'])

        self.assertDictEqual(
            person.data['relationships']['name_suffix'],
            {
                'data': {
                    'type': 'NameSuffix',
                    'id': '1764422'
                }
            }
        )

        self.assertEqual(
            suffix.id,
            person.rel.name_suffix.get().id
        )

        person.update()

        person2 = pco.people.people.get("23232372")
        suffix2 = person2.rel.name_suffix.get()

        self.assertEqual(suffix.id, suffix2.id)
        self.assertEqual(suffix.type, suffix2.type)

        # Assert we raise an exception if an object inheriting from BaseModel isn't passed
        with self.assertRaises(PCOInvalidModelError):
            person.rel.name_suffix.set(object())

        # Assert we raise an exception if the object has not been synced with PCO
        with self.assertRaises(PCOInvalidModelError):
            person.rel.name_suffix.set(pco.new(pypco.models.people.Person))

    def test_relationship_add(self):
        """Test adding a relationship in a to-many relationship.
        
        Note: This is a contrived example, since we're testing against the People
        API and there are no to-many relationships in the People API suitable
        for testing at this point.
        """

        pco = self.pco

        person_data = pco.people.people.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/23232378",
            params={
                "include":"addresses"
            }
        )['data']

        person = pypco.models.people.Person(
            pco.people.people,
            person_data,
            from_get = True
        )

        add_address = pco.people.addresses.get("28400159")

        person.rel.addresses.add(add_address)

        self.assertListEqual(
            person.data['relationships']['addresses']['data'],
            [
                {
                    'type': 'Address',
                    'id': '28400082'
                },
                {
                    'type': 'Address',
                    'id': '28400159'
                }
            ]
        )

        # Ensure we have an exception with a non-model object
        with self.assertRaises(PCOInvalidModelError):
            person.rel.addresses.add(object())

        # Ensure we have an exception if missing a type or id
        with self.assertRaises(PCOInvalidModelError):
            bad_address = pco.new(pypco.models.people.Address)
            person.rel.addresses.add(bad_address)

        # Ensure our model object is not newly created
        with self.assertRaises(PCOInvalidModelError):
            bad_address = pco.new(pypco.models.people.Address)
            bad_address._data['id'] = '123'
            person.rel.addresses.add(bad_address)

    def test_relationship_unset(self):
        """Test unsetting the object in a to-one relationship."""

        pco = self.pco

        person = pco.people.people.get("23232378")
        name_prefix = pco.people.name_prefixes.get("1764418")

        person.rel.name_prefix.set(name_prefix)
        person.update()

        person_name_prefix = person.rel.name_prefix.get()

        self.assertEqual(person_name_prefix.id, name_prefix.id)

        person.rel.name_prefix.unset()
        person.update()

        self.assertIsNone(person.rel.name_prefix.get())
    
    def test_relationship_remove(self):
        """Test removing an object in a to-many relationship.
        
        Note: This is a contrived example since we're testing against the People API
        and there don't appear to be any typical examples of to-many relationships
        of which we can avail ourselves for testing.
        """

        pco = self.pco

        person_data = pco.people.people.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/23232378",
            params={
                "include":"addresses"
            }
        )['data']

        person = pypco.models.people.Person(
            pco.people.people,
            person_data,
            from_get = True
        )

        addresses = [addr for addr in person.rel.addresses.list()]

        person.rel.addresses.remove(addresses[0])

        new_addresses = [addr for addr in person.rel.addresses.list()]

        self.assertNotIn(addresses[0].id, [addr.id for addr in new_addresses])
        self.assertIn(addresses[1].id, [addr.id for addr in new_addresses])

        # Exception must be thrown if we pass a model not currently present
        with self.assertRaises(PCOInvalidModelError):
            person.rel.addresses.remove(addresses[0])

        # Exception must be thrown if we don't pass a model
        with self.assertRaises(PCOInvalidModelError):
            person.rel.addresses.remove(object())

        # Exception must be thrown if we pass a model without type or id
        with self.assertRaises(PCOInvalidModelError):
            addr = pco.new(pypco.models.people.Address)
            addr._user_created = False
            person.rel.addresses.remove(addr)          

        # Exception must be thrown if we pass a model that is newly created
        with self.assertRaises(PCOInvalidModelError):
            person.rel.addresses.remove(pco.new(pypco.models.people.Address))

    def test_relationship_create(self):
        """Test creating objects that must be created from the related object's endpoint."""

        pco = self.pco

        # Test creating a new address
        person = pco.people.people.get("23232378")
        address = pco.new(pypco.models.people.Address)

        address.street = "123 Mount Vernon Rd"
        address.city = "Mount Vernon"
        address.state = "Va"
        address.zip = "11111"
        address.location = "Home"
        address.primary = True

        person.rel.addresses.create(address)

        address_from_person = [addr for addr in person.rel.addresses.list()][0]

        self.assertEqual(address.id, address_from_person.id)

        # Ensure an error is thrown if we pass a non-model object
        with self.assertRaises(PCOInvalidModelError):
            person.rel.addresses.create(object())

        # Ensure an error is thrown if we pass a model without a type
        with self.assertRaises(PCOInvalidModelError):
            bad_model = pco.new(pypco.models.people.Address)
            del bad_model._data['type']
            person.rel.addresses.create(bad_model)

        # Ensure an error is thrown if we pass a model that's not newly created
        with self.assertRaises(PCOInvalidModelError):
            person.rel.addresses.create(address)

    def test_add_on_new_object(self):
        """
        Test adding to-many relationships on a new object.

        An example of this in the People API would be creating households.
        """

        pco = self.pco

        lincolns = {
            'abraham': pco.people.people.get("35476772"),
            'mary': pco.people.people.get("35476793"),
            'robert': pco.people.people.get("35476796")
        }

        # Make sure we have people objects
        for name,person in lincolns.items(): #pylint: disable=W0612
            self.assertIsInstance(person, pypco.models.people.Person)

        household = pco.new(pypco.models.people.Household)

        # Set the household name
        household.name = "Lincoln Household"

        # Make sure we have a household object
        self.assertIsInstance(household, pypco.models.people.Household)
        household.rel.primary_contact.set(lincolns['abraham'])

        # Make sure primary contact is set
        self.assertEqual(lincolns['abraham'].id, household.rel.primary_contact.get().id)

        for name,person in lincolns.items():
            household.rel.people.add(person)

        hh_members = [member for member in household.rel.people.list()]
        hh_member_ids = [member.id for member in hh_members]

        # We should have three members
        self.assertEqual(len(hh_members), 3)

        # Make sure expected members are present
        for name,person in lincolns.items():
            self.assertIn(person.id, hh_member_ids)

        # Create the new household
        household.create()

        # Refresh the household object, for good measure
        household.refresh()

        # Check primary contact and members again on the refreshed copy

        # Make sure primary contact is set
        # Note that, oddly, this isn't returned as a relationship but
        # is instead returned as an attribute
        self.assertEqual(lincolns['abraham'].id, household.primary_contact_id)

        hh_members = [member for member in household.rel.people.list()]
        hh_member_ids = [member.id for member in hh_members]

        # We should have three members
        self.assertEqual(len(hh_members), 3)

        # Make sure expected members are present
        for name,person in lincolns.items():
            self.assertIn(person.id, hh_member_ids)