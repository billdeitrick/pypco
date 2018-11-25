"""Tests against PCO Resources."""

#pylint: disable=E1101

from .. import BasePCOVCRTestCase

class TestResources(BasePCOVCRTestCase):
    """Tests against PCO Resources."""

    def test_resources_list(self):
        """Verify that we can list resources."""

        pco = self.pco

        resources = [resource for resource in pco.resources.resources.list()]

        self.assertEqual(len(resources), 4)

        expected_names = [
            'Green Room [Sample]',
            'Main Auditorium [Sample]',
            'Food Table [Sample]',
            'Mobile Coffee Cart [Sample]'
        ]

        for name in expected_names:
            self.assertIn(name, expected_names)
