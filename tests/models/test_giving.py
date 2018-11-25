"""Tests against PCO Giving."""

#pylint: disable=E1101

from .. import BasePCOVCRTestCase

class TestGiving(BasePCOVCRTestCase):
    """Tests against PCO Giving."""

    def test_donations_list(self):
        """Verify that we can list donations."""

        pco = self.pco

        donations = [donation for donation in pco.giving.donations.list()]

        self.assertEqual(len(donations), 1)
        self.assertEqual(donations[0].amount_cents, 50000)
