"""Tests against PCO Services."""

#pylint: disable=E1101

from .. import BasePCOVCRTestCase

class TestServices(BasePCOVCRTestCase):
    """Tests against PCO Services."""

    def test_service_types_list(self):
        """Verify that we can list service types."""

        pco = self.pco

        service_types = [stype for stype in pco.services.service_types.list()]

        self.assertEqual(len(service_types), 1)
        self.assertEqual(service_types[0].name, 'Test Service Type')
