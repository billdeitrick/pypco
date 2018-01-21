"""Test the base PCO endpoint class"""
#pylint: disable=E1101,W0212

from unittest.mock import Mock, patch
from pypco.endpoints import PCOAuthConfig
from pypco.endpoints.base_endpoint import BaseEndpoint, NotValidRootEndpointError
from pypco.endpoints.people import PeopleEndpoint, People, Addresses, Stats, FieldDefinitions
from pypco.models.people import Person, Address, FieldDefinition
from tests import BasePCOTestCase

RL_REQ_COUNT = 0
RL_REQ_COUNT_PREV = 0

class TestBaseEndpoint(BasePCOTestCase):
    """Tests for the BasePCOEndpoint class."""

    def __init__(self, *args, **kwargs):
        """Initialize the TestBaseEndpoint TestCase."""

        BasePCOTestCase.__init__(self, *args, **kwargs)

        # Keep track of how many times we've created a rate limit mock
        self._rate_limit_mock_count = 0

    def test_base_endpoint_init(self):
        """Verify correct properties on the BaseEndpoint object."""

        auth_config = PCOAuthConfig("app_id", "app_secret")
        base_endpoint = BaseEndpoint(auth_config)

        self.assertIsInstance(base_endpoint._auth_config, PCOAuthConfig) #pylint: disable=W0212

    def test_get_auth_header(self):
        """Test generating the authentication header"""

        # Test basic auth header generation
        auth_config = PCOAuthConfig("app_id", "app_secret")
        base_endpoint = BaseEndpoint(auth_config)

        # Test getting the auth header the first time
        self.assertEqual(base_endpoint._get_auth_header(), "Basic YXBwX2lkOmFwcF9zZWNyZXQ=") #pylint: disable=W0212

        # Test getting the auth header the second time after it is cached
        self.assertEqual(base_endpoint._get_auth_header(), "Basic YXBwX2lkOmFwcF9zZWNyZXQ=") #pylint: disable=W0212

        # Test OAuth header generation
        auth_config = PCOAuthConfig(token="abc123")
        base_endpoint = BaseEndpoint(auth_config)

        # Test getting the auth header the first time
        self.assertEqual(base_endpoint._get_auth_header(), "Bearer abc123") #pylint: disable=W0212

        # Test getting the auth header the second time after it is cached
        self.assertEqual(base_endpoint._get_auth_header(), "Bearer abc123") #pylint: disable=W0212

    def test_check_rate_limit(self):
        """Test checking for a rate limited response."""

        # Check that we don't flag a successful response
        success = Mock()
        success.status_code = 200

        self.assertIsNone(BaseEndpoint._check_rate_limit_response(success)) #pylint: disable=W0212

        # Check that we do flag a rate limited response
        limited = Mock()
        limited.status_code = 429
        limited.headers = {'Retry-After': '10'}

        self.assertEqual(BaseEndpoint._check_rate_limit_response(limited), 10) #pylint: disable=W0212

    @patch('requests.request')
    @patch('time.sleep')
    def test_dispatch_get_success(self, mock_sleep, mock_get):
        """Test valid get request dispatching."""

        base_endpoint = BaseEndpoint(PCOAuthConfig("app_id", "secret'"))

        # Mock a simple response to our request
        response = Mock()
        response.status_code = 200
        response.headers = {}
        response.json = lambda: {
            "hello": "world"
        }
        mock_get.return_value = response

        result = base_endpoint._dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/1",
            {'bob': True}
        )

        # Make sure we fed the right params to requests.request
        mock_get.assert_called_with(
            'GET',
            'https://api.planningcenteronline.com/people/v2/people/1',
            headers={'Authorization': 'Basic YXBwX2lkOnNlY3JldCc='},
            params={'bob': True},
            json=None
        )

        # Make sure we didn't sleep...this was a valid response
        mock_sleep.assert_not_called()

        # make sure we got the expected result from our call
        self.assertEqual(result['hello'], 'world')

    def get_rate_limit_mock(method, url, headers, params, json): #pylint: disable=R0201,E0213,W0613
        """Create an object to mock rate limiting responses"""

        global RL_REQ_COUNT #pylint: disable=W0603
        global RL_REQ_COUNT_PREV #pylint: disable=W0603

        RL_REQ_COUNT = RL_REQ_COUNT_PREV
        RL_REQ_COUNT_PREV += 1

        class RateLimitResponse:
            """Mocking class for rate limited response

            When this class is called with a req_count > 0, it mock a successful
            request. Otherwise a rate limited request is mocked.
            """

            @property
            def status_code(self):
                """Mock the status code property"""

                if  RL_REQ_COUNT:
                    return 200

                return 429

            @property
            def headers(self):
                """Mock the headers property"""

                if RL_REQ_COUNT:
                    return {}

                return {"Retry-After": 5}

            @staticmethod
            def json():
                """Mock the json function"""

                if RL_REQ_COUNT:
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
                pass

        return RateLimitResponse()

    @patch('requests.request', side_effect=get_rate_limit_mock)
    @patch('time.sleep')
    def test_dispatch_get_limited(self, mock_sleep, mock_get):
        """Test request dispatching with rate limit"""

        base_endpoint = BaseEndpoint(PCOAuthConfig("app_id", "secret'"))

        result = base_endpoint._dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/1",
            {'bob': True}
        )

        # Make sure we fed the right params to requests.request
        mock_get.assert_called_with(
            'GET',
            'https://api.planningcenteronline.com/people/v2/people/1',
            headers={'Authorization': 'Basic YXBwX2lkOnNlY3JldCc='},
            params={'bob': True},
            json=None
        )

        mock_sleep.assert_called_once()

        # make sure we got the expected result from our call
        self.assertEqual(result['hello'], 'world')

    def test_resolve_class_name_endpoint(self): #pylint: disable=C0103
        """Test resolving class names to endpoint name."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "secret"))

        self.assertEqual(
            'people',
            people.resolve_root_endpoint_name()
        )

        with self.assertRaises(NotValidRootEndpointError):
            people.addresses.resolve_root_endpoint_name()

    def test_resolve_class_name_url(self):
        """Test resolving the class name to API url style."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "secret"))

        self.assertEqual(
            "people",
            people.people.resolve_class_name_url()
        )

        self.assertEqual(
            "addresses",
            people.addresses.resolve_class_name_url()
        )

        self.assertEqual(
            "field_definitions",
            people.field_definitions.resolve_class_name_url()
        )

    def test_get_full_endpoint_url(self):
        """Test the _get_upstream_url function."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "secret"))

        self.assertEqual(
            "https://api.planningcenteronline.com/people/v2",
            people.get_full_endpoint_url()
        )

        self.assertEqual(
            "https://api.planningcenteronline.com/people/v2/people",
            people.people.get_full_endpoint_url()
        )

        self.assertEqual(
            "https://api.planningcenteronline.com/people/v2/addresses",
            people.addresses.get_full_endpoint_url()
        )

        self.assertEqual(
            "https://api.planningcenteronline.com/people/v2/field_definitions",
            people.field_definitions.get_full_endpoint_url()
        )

    def test_resolve_model_type(self):
        """Test resolving PCO models based on returned object."""

        person = {
            "type": "Person"
        }

        self.assertEqual(
            People.resolve_model_type(person),
            ("people", "Person")
        )

        address = {
            "type": "Address"
        }

        self.assertEqual(
            Addresses.resolve_model_type(address),
            ("people", "Address")
        )

        field_definition = {
            "type": "FieldDefinition"
        }

        self.assertEqual(
            FieldDefinitions.resolve_model_type(field_definition),
            ("people", "FieldDefinition")
        )

        stats = {
            "type": "OrganizationalStatistics"
        }

        self.assertEqual(
            Stats.resolve_model_type(stats),
            ("people", "OrganizationalStatistics")
        )

    @patch('pypco.endpoints.people.People._dispatch_single_request')
    @patch('pypco.endpoints.people.Addresses._dispatch_single_request')
    @patch('pypco.endpoints.people.FieldDefinitions._dispatch_single_request')
    def test_people_get(self, mock_field_definition_request, mock_address_request, mock_people_request): #pylint: disable=C0301
        """Test retrieving mocked object by ID"""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"))

        # Test retrieving Person object by ID
        #region

        mock_people_request.return_value = {
            "data": {
                "type": "Person",
                "id": "25253",
                "attributes": {},
                "links": {}
            },
            "included": [],
            "meta": {}
        }

        result = people.people.get("25253")

        self.assertIsInstance(result, Person)

        #endregion

        # Test retrieving Address object by ID
        #region

        mock_address_request.return_value = {
            "data": {
                "type": "Address",
                "id": "25253",
                "attributes": {},
                "links": {}
            },
            "included": [],
            "meta": {}
        }

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"))
        result = people.addresses.get("25253")

        self.assertIsInstance(result, Address)

        #endregion

        # Test retrieving FieldDefinition object by ID
        #region
        mock_field_definition_request.return_value = {
            "data": {
                "type": "FieldDefinition",
                "id": "25253",
                "attributes": {},
                "links": {}
            },
            "included": [],
            "meta": {}
        }

        result = people.field_definitions.get("25253")

        self.assertIsInstance(result, FieldDefinition)

        #endregion
