"""Tests against PCO Webhooks."""

#pylint: disable=E1101

from .. import BasePCOVCRTestCase

class TestWebhooks(BasePCOVCRTestCase):
    """Tests against PCO Webhooks."""

    def test_available_events_list(self):
        """Verify that we can list available events."""

        pco = self.pco

        available_events = [event for event in pco.webhooks.available_events.list()]
        available_events_names = [event.name for event in available_events]

        self.assertEqual(len(available_events), 28)
        self.assertIn('people.v2.events.email.updated', available_events_names)
        self.assertIn('people.v2.events.person.updated', available_events_names)
