"""Test the primary pypco entry point -- the PCO object"""

#pylint: disable=protected-access

from unittest.mock import Mock, patch

import pypco
from tests import BasePCOTestCase, BasePCOVCRTestCase

class TestPrivateRequestFunctions(BasePCOTestCase):
    """Test low-level request mechanisms."""

    @patch('requests.request')
    @patch('builtins.open')
    def test_do_request(self, mock_fh, mock_request):
        """Test dispatching single requests; HTTP verbs, file uploads, etc."""

        # Setup PCO object and request mock
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret'
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"hello": "world"}'
        mock_request.return_value = mock_response

        # GET
        pco._do_request(
            'GET',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            include='test',
            per_page=100
        )

        mock_request.assert_called_with(
            'GET',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            params={
                'include':'test',
                'per_page':100
            },
            headers={
                'User-Agent': 'pypco',
                'Authorization': 'Basic YXBwX2lkOnNlY3JldA==',
            },
            json=None,
            timeout=60,
        )

        # POST
        pco._do_request(
            'POST',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            payload={
                'type': 'Person',
                'attributes': {
                    'a': 1,
                    'b': 2
                }
            }
        )

        mock_request.assert_called_with(
            'POST',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            json={
                'type': 'Person',
                'attributes': {
                    'a': 1,
                    'b': 2
                }
            },
            headers={
                'User-Agent': 'pypco',
                'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='
            },
            params={},
            timeout=60
        )

        # File Upload
        mock_fh.name = "open()"

        pco._do_request(
            'POST',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            upload='/file/path',
        )

        mock_fh.assert_called_once_with('/file/path', 'rb')

    def test_do_timeout_managed_request(self):
        pass

    def test_do_ratelimit_managed_request(self):
        pass

    def test_do_url_managed_request(self):
        pass

class TestPublicRequestFunctions(BasePCOVCRTestCase):
    """Test public PCO request functions."""
