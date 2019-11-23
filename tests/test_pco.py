"""Test the primary pypco entry point -- the PCO object"""

#pylint: disable=protected-access,global-statement

import json
from unittest.mock import Mock, patch

import requests

import pypco
from pypco.exceptions import PCORequestTimeoutException, \
    PCORequestException
from tests import BasePCOTestCase, BasePCOVCRTestCase

# Side effect functions and global vars

## Timeout testing
REQUEST_COUNT = 0
TIMEOUTS = 0

def timeout_se(*args, **kwargs):
    """A function to mock requests timeouts over multiple responses.

    You must set REQUEST_COUNT global variable to 0 and TIMEOUTS global variable to desired
    number before this function is be called.

    Returns:
        Mock: A mock response object.
    """

    global REQUEST_COUNT, TIMEOUTS #pylint: disable=global-statement

    REQUEST_COUNT += 1

    if REQUEST_COUNT == TIMEOUTS + 1:
        response = Mock()
        response.text = ''
        response.status_code = 200

        return response

    raise requests.exceptions.Timeout()

## Rate limit handling
RL_REQUEST_COUNT = 0
RL_LIMITED_REQUESTS = 0

def ratelimit_se(*args, **kwargs): #pylint: disable=unused-argument
    """Simulate rate limiting.

        You must define RL_REQUEST_COUNT and RL_LIMITED_REQUESTS as
        global variables before calling this function.

        Returns:
            Mock: A mock response object.
    """

    global RL_REQUEST_COUNT, RL_LIMITED_REQUESTS

    RL_LIMITED_REQUESTS += 1

    class RateLimitResponse:
        """Mocking class for rate limited response
        When this class is called with a req_count > 0, it mock a successful
        request. Otherwise a rate limited request is mocked.
        """

        @property
        def status_code(self):
            """Mock the status code property"""

            if  RL_LIMITED_REQUESTS > RL_REQUEST_COUNT:
                return 200

            return 429

        @property
        def headers(self):
            """Mock the headers property"""

            if RL_LIMITED_REQUESTS > RL_REQUEST_COUNT:
                return {}

            return {"Retry-After": RL_REQUEST_COUNT * 5}

        @property
        def text(self):
            """Mock the text property"""

            return json.dumps(RateLimitResponse.json())

        @staticmethod
        def json():
            """Mock the json function"""

            if RL_LIMITED_REQUESTS > RL_REQUEST_COUNT:
                return {
                    "hello": "world"
                }

            return {
                "errors": [
                    {
                        "code": "429",
                        "detail": "Rate limit exceeded: 118 of 100 requests per 20 seconds"
                    }
                ]
            }

        def raise_for_status(self):
            """Placeholder function for requests.response"""

    return RateLimitResponse()

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

    @patch('requests.request', side_effect=timeout_se)
    def test_do_timeout_managed_request(self, mock_request):
        """Test requests that automatically will retry on timeout."""

        global REQUEST_COUNT, TIMEOUTS

        # Setup PCO object and request mock
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret'
        )

        REQUEST_COUNT = 0
        TIMEOUTS = 0

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 1, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 1

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 2, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 1

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 2, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 2

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 3, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 3

        with self.assertRaises(PCORequestTimeoutException):
            pco._do_timeout_managed_request(
                'GET',
                '/test',
            )

        mock_request.assert_called_with(
            'GET',
            '/test',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

        # Let's try with only two retries permitted
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret',
            timeout_retries=2
        )

        REQUEST_COUNT = 0
        TIMEOUTS = 2

        with self.assertRaises(PCORequestTimeoutException):
            pco._do_timeout_managed_request(
                'GET',
                '/test',
            )

    @patch('requests.request', side_effect=ratelimit_se)
    @patch('time.sleep')
    def test_do_ratelimit_managed_request(self, mock_sleep, mock_request):
        """Test automatic rate limit handling."""

        global RL_REQUEST_COUNT, RL_LIMITED_REQUESTS

        # Setup PCO object
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret'
        )

        # Test with no rate limiting
        RL_REQUEST_COUNT = 0
        RL_LIMITED_REQUESTS = 0

        pco._do_ratelimit_managed_request(
            'GET',
            '/test'
        )

        mock_request.assert_called_once()
        mock_sleep.assert_not_called()

        # Test with rate limiting
        RL_REQUEST_COUNT = 1
        RL_LIMITED_REQUESTS = 0

        pco._do_ratelimit_managed_request(
            'GET',
            '/test'
        )

        mock_sleep.assert_called_once_with(5)

        # Test with rate limiting (three limited responses)
        RL_REQUEST_COUNT = 3
        RL_LIMITED_REQUESTS = 0

        result = pco._do_ratelimit_managed_request(
            'GET',
            '/test'
        )

        mock_sleep.assert_called_with(15)
        self.assertIsNotNone(result, "Didn't get response returned!")

    @patch('requests.request')
    def test_do_url_managed_request(self, mock_request):
        """Test requests with URL cleanup."""

        base = 'https://api.planningcenteronline.com'

        # Setup PCO object
        pco = pypco.PCO(
            base,
            application_id='app_id',
            secret='secret'
        )

        pco._do_url_managed_request('GET', '/test')

        mock_request.assert_called_with(
            'GET',
            f'{base}/test',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

        pco._do_url_managed_request('GET', 'https://api.planningcenteronline.com/test')

        mock_request.assert_called_with(
            'GET',
            f'{base}/test',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

        pco._do_url_managed_request('GET', 'https://api.planningcenteronline.com//test')

        mock_request.assert_called_with(
            'GET',
            f'{base}/test',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

        pco._do_url_managed_request('GET', 'https://api.planningcenteronline.com//test')

        mock_request.assert_called_with(
            'GET',
            f'{base}/test',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

        pco._do_url_managed_request('GET', \
            'https://api.planningcenteronline.com//test///test1/test2/////test3/test4')

        mock_request.assert_called_with(
            'GET',
            f'{base}/test/test1/test2/test3/test4',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

class TestPublicRequestFunctions(BasePCOVCRTestCase):
    """Test public PCO request functions."""

    def test_request_response(self):
        """Test the request_response function."""

        pco = self.pco

        response = pco.request_response('GET', '/people/v2/people')

        self.assertIsInstance(response, requests.Response, "Wrong type of object returned.")
        self.assertIsNotNone(response.json()['data'], "Expected to receive data but didn't.")

        with self.assertRaises(PCORequestException) as exception_ctxt:
            pco.request_response('GET', '/bogus')

        err = exception_ctxt.exception
        self.assertEqual(err.status_code, 404)

        with self.assertRaises(PCORequestException) as exception_ctxt:
            pco.request_response(
                'POST',
                '/people/v2/people',
                payload={}
            )

        err = exception_ctxt.exception
        self.assertEqual(err.status_code, 400)

    def test_request_json(self):
        """Test the request_json function."""

        pco = self.pco

        response = pco.request_json('GET', '/people/v2/people')

        self.assertIsInstance(response, dict)
        self.assertIsNotNone(response['data'])

        with self.assertRaises(PCORequestException) as exception_ctxt:
            pco.request_response('GET', '/bogus')

        err = exception_ctxt.exception
        self.assertEqual(err.status_code, 404)
