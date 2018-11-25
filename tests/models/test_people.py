"""Tests against PCO People."""

#pylint: disable=E1101

from .. import BasePCOVCRTestCase

class TestPeople(BasePCOVCRTestCase):
    """Tests against PCO People."""

    def test_people_list(self):
        """Verify that we can list people."""

        pco = self.pco

        people = [person for person in pco.people.people.list()]

        self.assertEqual(len(people), 1)
        self.assertEqual(people[0].name, 'Bill Deitrick')
