"""Test the primary pypco entry point -- the PCO object"""

#pylint: disable=protected-access,global-statement

import os
import json
from unittest.mock import Mock, patch

import requests
from requests.exceptions import SSLError

import pypco
from pypco.exceptions import PCORequestTimeoutException, \
    PCORequestException, PCOUnexpectedRequestException
from tests import BasePCOTestCase, BasePCOVCRTestCase

# region Side Effect Functions

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

def connection_error_se(*args, **kwargs):
    """Simulate a requests SSLError being thrown."""

    raise SSLError()

# endregion

class TestPrivateRequestFunctions(BasePCOTestCase):
    """Test low-level request mechanisms."""

    @patch('requests.Session.request')
    @patch('builtins.open')
    def test_do_request(self, mock_fh, mock_request):
        """Test dispatching single requests; HTTP verbs, file uploads, etc."""

        # Setup PCO object and request mock
        pco = pypco.PCO(
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

    @patch('requests.Session.request', side_effect=timeout_se)
    def test_do_timeout_managed_request(self, mock_request):
        """Test requests that automatically will retry on timeout."""

        global REQUEST_COUNT, TIMEOUTS

        # Setup PCO object and request mock
        pco = pypco.PCO(
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

    @patch('requests.Session.request', side_effect=ratelimit_se)
    @patch('time.sleep')
    def test_do_ratelimit_managed_request(self, mock_sleep, mock_request):
        """Test automatic rate limit handling."""

        global RL_REQUEST_COUNT, RL_LIMITED_REQUESTS

        # Setup PCO object
        pco = pypco.PCO(
            'app_id',
            'secret'
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

    @patch('requests.Session.request')
    def test_do_url_managed_request(self, mock_request):
        """Test requests with URL cleanup."""

        base = 'https://api.planningcenteronline.com'

        # Setup PCO object
        pco = pypco.PCO(
            'app_id',
            'secret'
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

    @patch('pypco.PCO._do_ratelimit_managed_request')
    def _test_do_url_managed_upload_request(self, mock_request):
        """Test upload request with URL cleanup (should ignore)."""

       # Setup PCO object
        pco = pypco.PCO(
            'app_id',
            'secret'
        )

        pco._do_url_managed_request(
            'POST',
            'https://upload.planningcenteronline.com/v2/files',
            upload='test',
        )

        mock_request.assert_called_with(
            'POST',
            'https://upload.planningcenteronline.com/v2/files',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            upload='test',
            json=None,
            params={},
            timeout=60
        )

class TestPublicRequestFunctions(BasePCOVCRTestCase):
    """Test public PCO request functions."""

    @patch('requests.Session.request', side_effect=connection_error_se)
    def test_request_resonse_general_err(self, mock_request): #pylint: disable=unused-argument
        """Test the request_response() function when a general error is thrown."""

        pco = self.pco

        with self.assertRaises(PCOUnexpectedRequestException):
            pco.request_response('GET', '/test')

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
        self.assertEqual(
            err.response_body,
            '{"errors":[{"status":"404","title":"Not Found",' \
                '"detail":"The resource you requested could not be found"}]}'
        )

        with self.assertRaises(PCORequestException) as exception_ctxt:
            pco.request_response(
                'POST',
                '/people/v2/people',
                payload={}
            )

        err = exception_ctxt.exception
        self.assertEqual(err.status_code, 400)
        self.assertEqual(
            err.response_body,
            '{"errors":[{"status":"400","title":"Bad Request",' \
                '"code":"invalid_resource_payload",' \
                    '"detail":"The payload given does not contain a \'data\' key."}]}'
        )

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

    def test_get(self):
        """Test the get function."""

        pco = self.pco

        # A basic get
        result = pco.get('/people/v2/people/45029164')
        self.assertEqual(result['data']['attributes']['name'], 'Paul Revere')

        # Get with includes
        result = pco.get('/people/v2/people/45029164', include='emails,organization')
        self.assertEqual(result['included'][0]['type'], 'Email')
        self.assertEqual(result['included'][0]['attributes']['address'], \
            'paul.revere@mailinator.com')
        self.assertEqual(result['included'][1]['type'], 'Organization')
        self.assertEqual(result['included'][1]['attributes']['name'], \
            'Pypco Dev')

        # Get with filter
        params = {
            'where[first_name]': 'paul'
        }

        result = pco.get('/people/v2/people', **params)
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['attributes']['first_name'], 'Paul')

    def test_post(self):
        """Test the post function."""

        pco = self.pco

        new_song = pco.template(
            'Song',
            {
                'title': 'Jesus Loves Me',
                'author': 'Public Domain'
            }
        )

        result = pco.post('/services/v2/songs', payload=new_song)

        self.assertEqual(result['data']['attributes']['title'], 'Jesus Loves Me')

    def test_patch(self):
        """Test the patch function."""

        pco = self.pco

        song = pco.template(
            'Song',
            {
                'author': 'Anna Bartlett Warner'
            }
        )

        response = pco.patch('/services/v2/songs/18338876', song)

        self.assertEqual(response['data']['attributes']['title'], 'Jesus Loves Me')
        self.assertEqual(response['data']['attributes']['author'], 'Anna Bartlett Warner')

    def test_delete(self):
        """Test the delete function."""

        pco = self.pco

        response = pco.delete('/services/v2/songs/18420243')

        self.assertEqual(response.status_code, 204)

        with self.assertRaises(PCORequestException):
            pco.get('/services/v2/songs/18420243')

    def test_iterate(self):
        """Test the iterate function."""

        pco = self.pco

        # Get all people w/ default page size of 25
        all_people = [row for row in pco.iterate('/people/v2/people')]
        self.assertEqual(200, len(all_people), 'Should have been 200 results in People query.')

        # Make sure we got all 200 unique ids
        id_set = {person['data']['id'] for person in all_people}
        self.assertEqual(200, len(id_set), 'Expected 200 unique people ids.')

        # Change default page size to 50
        all_people = [row for row in pco.iterate('/people/v2/people', per_page=50)]
        self.assertEqual(200, len(all_people), 'Should have been 200 results in People query.')

        # Make sure we got all 200 unique ids
        id_set = {person['data']['id'] for person in all_people}
        self.assertEqual(200, len(id_set), 'Expected 200 unique people ids.')

        # Start with a non-zero offset
        all_people = [row for row in pco.iterate('/people/v2/people', offset=25)]
        self.assertEqual(175, len(all_people), 'Should have been 150 results in People query.')

        # Make sure we got all 200 unique ids
        id_set = {person['data']['id'] for person in all_people}
        self.assertEqual(175, len(id_set), 'Expected 150 unique people ids.')

        # Get a single include, excluding admins to avoid publishing email in VCR data
        query = {
            'where[site_administrator]': 'false',
        }

        all_people = [row for row in pco.iterate('/people/v2/people', include='emails', **query)]
        self.assertEqual(199, len(all_people), 'Query did not return expected number of people.')

        for person in all_people:
            self.assertEqual(1, len(person['included']), 'Expected exactly one include.')
            self.assertEqual('Email', person['included'][0]['type'], 'Unexpected include type.')
            self.assertEqual(
                person['data']['relationships']['emails']['data'][0]['id'],
                person['included'][0]['id'],
                'Email id did not match as expected.'
            )

        # Test multiple includes, again excluding admins
        query = {
            'where[site_administrator]': 'false',
        }

        all_people = [row for row in pco.iterate(
            '/people/v2/people',
            include='emails,organization',
            **query
        )]

        for person in all_people:
            self.assertEqual(2, len(person['included']), 'Expected exactly two includes.')

            for included in person['included']:
                self.assertIn(
                    included['type'],
                    ['Email', 'Organization'],
                    'Unexpected include type'
                )

                if included['type'] == 'Email':
                    self.assertEqual(
                        included['relationships']['person']['data']['id'],
                        person['data']['id'],
                        'Email id did not match as expected.'
                    )

        # Test multiple included objects of same type
        query = {
            'where[first_name]': 'Paul',
        }

        all_pauls = [row for row in pco.iterate('/people/v2/people', include='addresses', **query)]

        self.assertEqual(2, len(all_pauls), 'Unexpected number of people returned.')

        for person in all_pauls:

            included_person_ids = set()

            for included in person['included']:
                self.assertEqual(included['type'], 'Address')
                included_person_ids.add(included['relationships']['person']['data']['id'])

            self.assertEqual(1, len(included_person_ids))
            self.assertEqual(included_person_ids.pop(), person['data']['id'])

    def test_iterate_no_relationships(self):
        """Test iterate when the relationships attribute is missing."""

        pco = self.pco

        report_templates = [record for record in pco.iterate('/services/v2/report_templates')]

        self.assertEqual(
            36,
            len(report_templates),
            'Unexpected number of report templates returned.'
        )

    def test_template(self):
        """Test the template function."""

        pco = self.pco

        template = pco.template('Test')

        self.assertEqual(
            template,
            {
                'data': {
                    'type': 'Test',
                    'attributes': {}
                }
            }
        )

        template = pco.template('Test2', {'test_attr': 'hello'})

        self.assertEqual(
            template,
            {
                'data': {
                    'type': 'Test2',
                    'attributes': {
                        'test_attr': 'hello'
                    }
                }
            }
        )

    def test_upload(self):
        """Test the file upload function."""

        pco = self.pco

        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = '/assets/test_upload.jpg'

        upload_response = pco.upload(f'{base_path}{file_path}')

        self.assertEqual(upload_response['data'][0]['type'], 'File')
        self.assertIsInstance(upload_response['data'][0]['id'], str)
        self.assertEqual(upload_response['data'][0]['attributes']['name'], 'test_upload.jpg')

    def test_upload_and_use_file(self):
        """Verify we can use an uploaded file in PCO."""

        pco = self.pco

        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = '/assets/test_upload.jpg'

        upload_response = pco.upload(f'{base_path}{file_path}')

        query = {
            'where[first_name]': 'Paul',
            'where[last_name]': 'Revere',
        }

        paul = next(pco.iterate('/people/v2/people', **query))

        user_template = pco.template('Person', {'avatar': upload_response['data'][0]['id']})

        patch_result = pco.patch(paul['data']['links']['self'], user_template)

        self.assertNotRegex(patch_result['data']['attributes']['avatar'], r'.*no_photo_thumbnail.*')

class TestPCOInitialization(BasePCOTestCase):
    """Test initializing PCO objects with various argument combinations."""

    def test_pco_initialization(self):
        """Test initializing the PCO object with various combinations of arguments."""

        # region Minimal Args: PAT Auth
        pco = pypco.PCO(
            'app_id',
            'app_secret',
        )

        self.assertIsInstance(pco._auth_config, pypco.auth_config.PCOAuthConfig)
        self.assertIsInstance(pco._auth_header, str)
        self.assertEqual(pco.api_base, 'https://api.planningcenteronline.com')
        self.assertEqual(pco.timeout, 60)
        self.assertEqual(pco.upload_url, 'https://upload.planningcenteronline.com/v2/files')
        self.assertEqual(pco.upload_timeout, 300)
        self.assertEqual(pco.timeout_retries, 3)

        # endregion

        # region Minimal Args: OAUTH
        pco = pypco.PCO(
            token='abc'
        )

        self.assertIsInstance(pco._auth_config, pypco.auth_config.PCOAuthConfig)
        self.assertIsInstance(pco._auth_header, str)
        self.assertEqual(pco.api_base, 'https://api.planningcenteronline.com')
        self.assertEqual(pco.timeout, 60)
        self.assertEqual(pco.upload_url, 'https://upload.planningcenteronline.com/v2/files')
        self.assertEqual(pco.upload_timeout, 300)
        self.assertEqual(pco.timeout_retries, 3)

        # endregion

        # region: Change all defaults
        pco = pypco.PCO(
            'app_id',
            'app_secret',
            api_base='https://bogus.base',
            timeout=120,
            upload_url='https://upload.files',
            upload_timeout=50,
            timeout_retries=500,
        )

        self.assertIsInstance(pco._auth_config, pypco.auth_config.PCOAuthConfig)
        self.assertIsInstance(pco._auth_header, str)
        self.assertEqual(pco.api_base, 'https://bogus.base')
        self.assertEqual(pco.timeout, 120)
        self.assertEqual(pco.upload_url, 'https://upload.files')
        self.assertEqual(pco.upload_timeout, 50)
        self.assertEqual(pco.timeout_retries, 500)
