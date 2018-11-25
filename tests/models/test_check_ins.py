"""Tests against PCO Check-Ins."""

#pylint: disable=E1101

from .. import BasePCOVCRTestCase

class TestCheckIns(BasePCOVCRTestCase):
    """Tests against PCO Check-Ins."""

    def test_events_list(self):
        """Verify that we can list events."""

        pco = self.pco

        events = [event for event in pco.check_ins.events.list()]

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].name, 'Weekly Worship Services')
