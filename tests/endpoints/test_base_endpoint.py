"""Test the base PCO endpoint class"""
#pylint: disable=E1101,W0212

import unittest
import json as jsonlib
from unittest.mock import Mock, patch
from pypco.endpoints import PCOAuthConfig
from pypco.endpoints.base_endpoint import BaseEndpoint, NotValidRootEndpointError, PCOAPIMethod
from pypco.endpoints.people import PeopleEndpoint, People, Addresses, Stats, FieldDefinitions
from pypco.endpoints.check_ins import CheckInsEndpoint
from pypco.models.people import Person, Address, FieldDefinition, Email
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
        base_endpoint = BaseEndpoint(auth_config, None)

        self.assertIsInstance(base_endpoint._auth_config, PCOAuthConfig) #pylint: disable=W0212
        self.assertIsNone(base_endpoint._api_instance)

    def test_get_auth_header(self):
        """Test generating the authentication header"""

        # Test basic auth header generation
        auth_config = PCOAuthConfig("app_id", "app_secret")
        base_endpoint = BaseEndpoint(auth_config, None)

        # Test getting the auth header the first time
        self.assertEqual(base_endpoint._get_auth_header(), "Basic YXBwX2lkOmFwcF9zZWNyZXQ=") #pylint: disable=W0212

        # Test getting the auth header the second time after it is cached
        self.assertEqual(base_endpoint._get_auth_header(), "Basic YXBwX2lkOmFwcF9zZWNyZXQ=") #pylint: disable=W0212

        # Test OAuth header generation
        auth_config = PCOAuthConfig(token="abc123")
        base_endpoint = BaseEndpoint(auth_config, None)

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

        base_endpoint = BaseEndpoint(PCOAuthConfig("app_id", "secret"), None)

        # Mock a simple response to our request
        response = Mock()
        response.status_code = 200
        response.headers = {}
        response.text = '{ "hello": "world" }'
        response.json = lambda: {
            "hello": "world"
        }
        mock_get.return_value = response

        result = base_endpoint.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/1",
            {'bob': True}
        )

        # Make sure we fed the right params to requests.request
        mock_get.assert_called_with(
            'GET',
            'https://api.planningcenteronline.com/people/v2/people/1',
            headers={'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            params={'bob': True},
            json=None
        )

        # Make sure we didn't sleep...this was a valid response
        mock_sleep.assert_not_called()

        # make sure we got the expected result from our call
        self.assertEqual(result['hello'], 'world')

    @patch('requests.request')
    def test_dispatch_empty_response(self, mock_delete):
        """Verify we handle empty API responses gracefully"""

        base_endpoint = BaseEndpoint(PCOAuthConfig("app_id", "secret"), None)

        # Mock a simple response to our request
        response = Mock()
        response.status_code = 204
        response.headers = {}
        response.text = ""
        response.json = lambda: 1/0

        result = base_endpoint.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/1",
            method=PCOAPIMethod.DELETE
        )

        self.assertEqual(result, {})        

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

            @property
            def text(self):
                """Mock the text property"""

                return jsonlib.dumps(RateLimitResponse.json())

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

        base_endpoint = BaseEndpoint(PCOAuthConfig("app_id", "secret"), None)

        result = base_endpoint.dispatch_single_request(
            "https://api.planningcenteronline.com/people/v2/people/1",
            {'bob': True}
        )

        # Make sure we fed the right params to requests.request
        mock_get.assert_called_with(
            'GET',
            'https://api.planningcenteronline.com/people/v2/people/1',
            headers={'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            params={'bob': True},
            json=None
        )

        mock_sleep.assert_called_once()

        # make sure we got the expected result from our call
        self.assertEqual(result['hello'], 'world')

    def test_resolve_class_name_endpoint(self): #pylint: disable=C0103
        """Test resolving class names to endpoint name."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "secret"), None)

        self.assertEqual(
            'people',
            people.resolve_root_endpoint_name()
        )

        with self.assertRaises(NotValidRootEndpointError):
            people.addresses.resolve_root_endpoint_name()

        checkins = CheckInsEndpoint(PCOAuthConfig("app_id", "secret"), None)

        self.assertEqual(
            'check_ins',
            checkins.resolve_root_endpoint_name()
        )

    def test_resolve_class_name_url(self):
        """Test resolving the class name to API url style."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "secret"), None)

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

        people = PeopleEndpoint(PCOAuthConfig("app_id", "secret"), None)

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

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    @patch('pypco.endpoints.people.Addresses.dispatch_single_request')
    @patch('pypco.endpoints.people.FieldDefinitions.dispatch_single_request')
    def test_people_get(self, mock_field_definition_request, mock_address_request, mock_people_request): #pylint: disable=C0301
        """Test retrieving mocked object by ID"""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

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

        mock_people_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/people/25253"
        )
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

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)
        result = people.addresses.get("25253")

        mock_address_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/addresses/25253"
        )
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

        mock_field_definition_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/field_definitions/25253"
        )
        self.assertIsInstance(result, FieldDefinition)

        #endregion

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    def test_people_list(self, mock_people_request):
        """Test the list function to query endpoints."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        # Mock retrieving people over multiple pages with a simple query
        # This validates search parameters and multiple pages of results
        #region

        # Mock page one of the search results for people
        # with the last name "Revere" and a page size of 2
        mock_people_request.return_value = {
            "links": {
                "self": "https://api.planningcenteronline.com/people/v2/people?per_page=2&where[last_name]=Revere",
                "next": "https://api.planningcenteronline.com/people/v2/people?offset=2&per_page=2&where[last_name]=Revere"
            },
            "data": [
                {
                    "type": "Person",
                    "id": "16555904",
                    "attributes": {
                        "anniversary": None,
                        "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                        "birthdate": "1916-01-01",
                        "child": False,
                        "created_at": "2016-04-23T01:19:54Z",
                        "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                        "first_name": "Paul",
                        "gender": "M",
                        "given_name": None,
                        "grade": None,
                        "graduation_year": None,
                        "inactivated_at": None,
                        "last_name": "Revere",
                        "medical_notes": None,
                        "membership": "Participant",
                        "middle_name": None,
                        "name": "Paul Revere",
                        "nickname": None,
                        "people_permissions": "Editor",
                        "remote_id": None,
                        "school_type": None,
                        "site_administrator": False,
                        "status": "active",
                        "updated_at": "2017-12-11T19:10:41Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/people/16555904"
                    }
                },
                {
                    "type": "Person",
                    "id": "25423946",
                    "attributes": {
                        "anniversary": None,
                        "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                        "birthdate": None,
                        "child": False,
                        "created_at": "2017-04-11T22:42:08Z",
                        "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                        "first_name": "Paul",
                        "gender": "M",
                        "given_name": None,
                        "grade": None,
                        "graduation_year": None,
                        "inactivated_at": None,
                        "last_name": "Revere",
                        "medical_notes": None,
                        "membership": "Former Attender",
                        "middle_name": None,
                        "name": "Paul Revere Jr.",
                        "nickname": None,
                        "people_permissions": None,
                        "remote_id": None,
                        "school_type": None,
                        "site_administrator": False,
                        "status": "active",
                        "updated_at": "2017-04-12T00:28:13Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/people/25423946"
                    }
                }
            ],
            "included": [],
            "meta": {
                "total_count": 4,
                "count": 2,
                "next": {
                    "offset": 2
                },
                "can_order_by": [
                    "given_name",
                    "first_name",
                    "nickname",
                    "middle_name",
                    "last_name",
                    "birthdate",
                    "anniversary",
                    "gender",
                    "grade",
                    "child",
                    "status",
                    "school_type",
                    "graduation_year",
                    "site_administrator",
                    "people_permissions",
                    "membership",
                    "inactivated_at",
                    "remote_id",
                    "medical_notes",
                    "created_at",
                    "updated_at"
                ],
                "can_query_by": [
                    "given_name",
                    "first_name",
                    "nickname",
                    "middle_name",
                    "last_name",
                    "birthdate",
                    "anniversary",
                    "gender",
                    "grade",
                    "child",
                    "status",
                    "school_type",
                    "graduation_year",
                    "site_administrator",
                    "people_permissions",
                    "membership",
                    "inactivated_at",
                    "remote_id",
                    "medical_notes",
                    "created_at",
                    "updated_at",
                    "search_name",
                    "search_name_or_email",
                    "id"
                ],
                "can_include": [
                    "addresses",
                    "emails",
                    "field_data",
                    "households",
                    "inactive_reason",
                    "marital_status",
                    "name_prefix",
                    "name_suffix",
                    "person_apps",
                    "phone_numbers",
                    "school",
                    "social_profiles"
                ],
                "can_filter": [
                    "created_since",
                    "admins",
                    "organization_admins"
                ],
                "parent": {
                    "id": "197716",
                    "type": "Organization"
                }
            }
        }

        results = people.people.list(where={'last_name': 'Revere'}, per_page=2)
        result_count = 0

        for result in results:
            result_count += 1

            self.assertIsInstance(result, Person)

            # Verify we've called the first request with correct params
            if result_count == 1:
                mock_people_request.assert_called_with(
                    'https://api.planningcenteronline.com/people/v2/people',
                    params = [
                        ('where[last_name]', 'Revere'),
                        ('per_page', 2)
                    ]
                )

            # Mock the second page of search results
            elif result_count == 2:            
                mock_people_request.return_value = {
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/people?offset=2&per_page=2&where[last_name]=Revere",
                        "prev": "https://api.planningcenteronline.com/people/v2/people?offset=0&per_page=2&where[last_name]=Revere"
                    },
                    "data": [
                        {
                            "type": "Person",
                            "id": "25423947",
                            "attributes": {
                                "anniversary": None,
                                "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_woman_gray.svg",
                                "birthdate": None,
                                "child": False,
                                "created_at": "2017-04-11T22:42:09Z",
                                "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_woman_gray.svg",
                                "first_name": "Rachel",
                                "gender": "F",
                                "given_name": None,
                                "grade": None,
                                "graduation_year": None,
                                "inactivated_at": None,
                                "last_name": "Revere",
                                "medical_notes": None,
                                "membership": "Former Attender",
                                "middle_name": None,
                                "name": "Rachel Revere",
                                "nickname": None,
                                "people_permissions": None,
                                "remote_id": None,
                                "school_type": None,
                                "site_administrator": False,
                                "status": "active",
                                "updated_at": "2017-04-12T00:28:14Z"
                            },
                            "links": {
                                "self": "https://api.planningcenteronline.com/people/v2/people/25423947"
                            }
                        },
                        {
                            "type": "Person",
                            "id": "31515549",
                            "attributes": {
                                "anniversary": None,
                                "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_gray.svg",
                                "birthdate": None,
                                "child": False,
                                "created_at": "2017-11-17T15:52:06Z",
                                "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_gray.svg",
                                "first_name": "Rachel",
                                "gender": None,
                                "given_name": None,
                                "grade": None,
                                "graduation_year": None,
                                "inactivated_at": None,
                                "last_name": "Revere",
                                "medical_notes": None,
                                "membership": None,
                                "middle_name": None,
                                "name": "Rachel Revere",
                                "nickname": None,
                                "people_permissions": None,
                                "remote_id": 77953914,
                                "school_type": None,
                                "site_administrator": False,
                                "status": "active",
                                "updated_at": "2017-11-17T15:52:06Z"
                            },
                            "links": {
                                "self": "https://api.planningcenteronline.com/people/v2/people/31515549"
                            }
                        }
                    ],
                    "included": [],
                    "meta": {
                        "total_count": 4,
                        "count": 2,
                        "prev": {
                            "offset": 0
                        },
                        "can_order_by": [
                            "given_name",
                            "first_name",
                            "nickname",
                            "middle_name",
                            "last_name",
                            "birthdate",
                            "anniversary",
                            "gender",
                            "grade",
                            "child",
                            "status",
                            "school_type",
                            "graduation_year",
                            "site_administrator",
                            "people_permissions",
                            "membership",
                            "inactivated_at",
                            "remote_id",
                            "medical_notes",
                            "created_at",
                            "updated_at"
                        ],
                        "can_query_by": [
                            "given_name",
                            "first_name",
                            "nickname",
                            "middle_name",
                            "last_name",
                            "birthdate",
                            "anniversary",
                            "gender",
                            "grade",
                            "child",
                            "status",
                            "school_type",
                            "graduation_year",
                            "site_administrator",
                            "people_permissions",
                            "membership",
                            "inactivated_at",
                            "remote_id",
                            "medical_notes",
                            "created_at",
                            "updated_at",
                            "search_name",
                            "search_name_or_email",
                            "id"
                        ],
                        "can_include": [
                            "addresses",
                            "emails",
                            "field_data",
                            "households",
                            "inactive_reason",
                            "marital_status",
                            "name_prefix",
                            "name_suffix",
                            "person_apps",
                            "phone_numbers",
                            "school",
                            "social_profiles"
                        ],
                        "can_filter": [
                            "created_since",
                            "admins",
                            "organization_admins"
                        ],
                        "parent": {
                            "id": "197716",
                            "type": "Organization"
                        }
                    }
                }

            # Verify we've called the second request with correct params
            if result_count == 3:
                mock_people_request.assert_called_with(
                    'https://api.planningcenteronline.com/people/v2/people',
                    params = [                        
                        ('where[last_name]', 'Revere'),
                        ('per_page', 2),
                        ('offset', 2)
                    ]
                )

        # Verify we've iterated through 4 results as expected
        self.assertEqual(result_count, 4)
        
        #endregion

        # Mock retrieving people with different sets of parameters
        # We'll mock a request that returns no results
        #region
        mock_people_request.return_value = {
            "links": {
                "self": "https://api.planningcenteronline.com/people/v2/people?offset=2&per_page=2&where[last_name]=NotAResult",
                "prev": "https://api.planningcenteronline.com/people/v2/people?offset=0&per_page=2&where[last_name]=NotAResult"
            },
            "data": [],
            "included": [],
            "meta": {
                "total_count": 0,
                "count": 0,
                "prev": {
                    "offset": 0
                },
                "can_order_by": [
                    "given_name",
                    "first_name",
                    "nickname",
                    "middle_name",
                    "last_name",
                    "birthdate",
                    "anniversary",
                    "gender",
                    "grade",
                    "child",
                    "status",
                    "school_type",
                    "graduation_year",
                    "site_administrator",
                    "people_permissions",
                    "membership",
                    "inactivated_at",
                    "remote_id",
                    "medical_notes",
                    "created_at",
                    "updated_at"
                ],
                "can_query_by": [
                    "given_name",
                    "first_name",
                    "nickname",
                    "middle_name",
                    "last_name",
                    "birthdate",
                    "anniversary",
                    "gender",
                    "grade",
                    "child",
                    "status",
                    "school_type",
                    "graduation_year",
                    "site_administrator",
                    "people_permissions",
                    "membership",
                    "inactivated_at",
                    "remote_id",
                    "medical_notes",
                    "created_at",
                    "updated_at",
                    "search_name",
                    "search_name_or_email",
                    "id"
                ],
                "can_include": [
                    "addresses",
                    "emails",
                    "field_data",
                    "households",
                    "inactive_reason",
                    "marital_status",
                    "name_prefix",
                    "name_suffix",
                    "person_apps",
                    "phone_numbers",
                    "school",
                    "social_profiles"
                ],
                "can_filter": [
                    "created_since",
                    "admins",
                    "organization_admins"
                ],
                "parent": {
                    "id": "197716",
                    "type": "Organization"
                }
            }
        }

        # A set of "where" params to re-use
        wheres = {
            'first_name': 'pico',
            'last_name': 'robot'
        }

        # Test a query with just "where" params
        #region
        results = [result for result in people.people.list(
            where = {
                'first_name': 'pico',
                'last_name': 'robot'
            }
        )]

        self.assertEqual(len(results), 0)
        mock_people_request.assert_called_with(
            'https://api.planningcenteronline.com/people/v2/people',
            params = [
                ('where[first_name]', 'pico'),
                ('where[last_name]', 'robot'),
            ]
        )
        #endregion

        # Test a query with "where" and filter params
        #region
        results = [result for result in people.people.list(
            wheres,
            filter=[
                'admins',
                'created_since'
            ]
        )]

        self.assertEqual(len(results), 0)
        mock_people_request.assert_called_with(
            'https://api.planningcenteronline.com/people/v2/people',
            params=[
                ('where[first_name]', 'pico'),
                ('where[last_name]', 'robot'),
                ('filter', 'admins'),
                ('filter', 'created_since')
            ]
        )
        #endregion

        # Test a query with "where" and "per_page" params
        #region
        results = [result for result in people.people.list(
            wheres,
            per_page=5
        )]

        self.assertEqual(len(results), 0)
        mock_people_request.assert_called_with(
            'https://api.planningcenteronline.com/people/v2/people',
            params=[
                ('where[first_name]', 'pico'),
                ('where[last_name]', 'robot'),
                ('per_page', 5)
            ]
        )
        #endregion

        # Test a query with "where" and "order" params
        #region
        results = [result for result in people.people.list(
            wheres,
            order='birthdate'
        )]

        self.assertEqual(len(results), 0)
        mock_people_request.assert_called_with(
            'https://api.planningcenteronline.com/people/v2/people',
            params=[
                ('where[first_name]', 'pico'),
                ('where[last_name]', 'robot'),
                ('order', 'birthdate')
            ]
        )
        #endregion

        # Test a query with "where" and a kwarg
        #region
        results = [result for result in people.people.list(
            wheres,
            custom_kwarg = "abc123"
        )]

        self.assertEqual(len(results), 0)
        mock_people_request.assert_called_with(
            'https://api.planningcenteronline.com/people/v2/people',
            params=[
                ('where[first_name]', 'pico'),
                ('where[last_name]', 'robot'),
                ('custom_kwarg', 'abc123')
            ]
        )
        #endregion

        # The kitchen sink test...a query with all params.
        #region
        results = [result for result in people.people.list(
            wheres,
            filter = ['admins'],
            per_page = 11,
            order = 'birthdate',
            custom_kwarg = "abc123"
        )]

        self.assertEqual(len(results), 0)
        mock_people_request.assert_called_with(
            'https://api.planningcenteronline.com/people/v2/people',
            params=[
                ('where[first_name]', 'pico'),
                ('where[last_name]', 'robot'),
                ('filter', 'admins'),
                ('per_page', 11),
                ('order', 'birthdate'),
                ('custom_kwarg', 'abc123')
            ]
        )
        #endregion

        #endregion

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    def test_people_delete(self, mock_people_request):
        """Test delete function to delete objects from the PCO API."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        # Mock an empty response for a deleted person
        mock_people_request.return_value = {}

        people.people.delete("https://api.planningcenteronline.com/people/v2/people/25253")

        mock_people_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/people/25253",
            method = PCOAPIMethod.DELETE
        )

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    def test_people_update(self, mock_people_request):
        """Test updating a mocked object using the update function."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        mock_people_request.return_value = {
            "data": {
                "type": "Person",
                "id": "34765191",
                "attributes": {
                    "anniversary": None,
                    "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                    "birthdate": None,
                    "child": False,
                    "created_at": "2018-02-20T20:59:57Z",
                    "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                    "first_name": "Pico",
                    "gender": "M",
                    "given_name": None,
                    "grade": None,
                    "graduation_year": None,
                    "inactivated_at": None,
                    "last_name": "Robot",
                    "medical_notes": None,
                    "membership": None,
                    "middle_name": None,
                    "name": "Pico Robot",
                    "nickname": None,
                    "people_permissions": None,
                    "remote_id": None,
                    "school_type": None,
                    "site_administrator": False,
                    "status": "active",
                    "updated_at": "2018-02-20T21:15:29Z"
                },
                "links": {
                    "addresses": "https://api.planningcenteronline.com/people/v2/people/34765191/addresses",
                    "apps": "https://api.planningcenteronline.com/people/v2/people/34765191/apps",
                    "connected_people": "https://api.planningcenteronline.com/people/v2/people/34765191/connected_people",
                    "emails": "https://api.planningcenteronline.com/people/v2/people/34765191/emails",
                    "field_data": "https://api.planningcenteronline.com/people/v2/people/34765191/field_data",
                    "household_memberships": "https://api.planningcenteronline.com/people/v2/people/34765191/household_memberships",
                    "households": "https://api.planningcenteronline.com/people/v2/people/34765191/households",
                    "inactive_reason": None,
                    "marital_status": None,
                    "message_groups": "https://api.planningcenteronline.com/people/v2/people/34765191/message_groups",
                    "messages": "https://api.planningcenteronline.com/people/v2/people/34765191/messages",
                    "name_prefix": None,
                    "name_suffix": None,
                    "person_apps": "https://api.planningcenteronline.com/people/v2/people/34765191/person_apps",
                    "phone_numbers": "https://api.planningcenteronline.com/people/v2/people/34765191/phone_numbers",
                    "school": None,
                    "social_profiles": "https://api.planningcenteronline.com/people/v2/people/34765191/social_profiles",
                    "workflow_cards": "https://api.planningcenteronline.com/people/v2/people/34765191/workflow_cards",
                    "self": "https://api.planningcenteronline.com/people/v2/people/34765191"
                }
            },
            "included": [],
            "meta": {
                "can_include": [
                    "addresses",
                    "emails",
                    "field_data",
                    "households",
                    "inactive_reason",
                    "marital_status",
                    "name_prefix",
                    "name_suffix",
                    "person_apps",
                    "phone_numbers",
                    "school",
                    "social_profiles"
                ],
                "parent": {
                    "id": "197716",
                    "type": "Organization"
                }
            }
        }

        result = people.people.update(
            "https://api.planningcenteronline.com/people/v2/people/34765191", 
            {
                "data": {
                    "type": "Person",
                    "id": "34765191",
                    "attributes": {
                        "gender": "Male"
                    }
                }
            }
        )

        mock_people_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/people/34765191",
            payload = {
                "data": {
                    "type": "Person",
                    "id": "34765191",
                    "attributes": {
                        "gender": "Male"
                    }
                }
            },
            method = PCOAPIMethod.PATCH
        )

        self.assertEqual(result['data']['attributes']['gender'], 'M')

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    def test_get_by_url(self, mock_people_request):
        """Test getting objects from PCO API directly by URL"""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        mock_people_request.return_value = {
            "data": {
                "type": "Person",
                "id": "34765191",
                "attributes": {
                    "anniversary": None,
                    "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                    "birthdate": None,
                    "child": False,
                    "created_at": "2018-02-20T20:59:57Z",
                    "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                    "first_name": "Pico",
                    "gender": "M",
                    "given_name": None,
                    "grade": None,
                    "graduation_year": None,
                    "inactivated_at": None,
                    "last_name": "Robot",
                    "medical_notes": None,
                    "membership": None,
                    "middle_name": None,
                    "name": "Pico Robot",
                    "nickname": None,
                    "people_permissions": None,
                    "remote_id": None,
                    "school_type": None,
                    "site_administrator": False,
                    "status": "active",
                    "updated_at": "2018-02-20T21:15:29Z"
                },
                "links": {
                    "addresses": "https://api.planningcenteronline.com/people/v2/people/34765191/addresses",
                    "apps": "https://api.planningcenteronline.com/people/v2/people/34765191/apps",
                    "connected_people": "https://api.planningcenteronline.com/people/v2/people/34765191/connected_people",
                    "emails": "https://api.planningcenteronline.com/people/v2/people/34765191/emails",
                    "field_data": "https://api.planningcenteronline.com/people/v2/people/34765191/field_data",
                    "household_memberships": "https://api.planningcenteronline.com/people/v2/people/34765191/household_memberships",
                    "households": "https://api.planningcenteronline.com/people/v2/people/34765191/households",
                    "inactive_reason": None,
                    "marital_status": None,
                    "message_groups": "https://api.planningcenteronline.com/people/v2/people/34765191/message_groups",
                    "messages": "https://api.planningcenteronline.com/people/v2/people/34765191/messages",
                    "name_prefix": None,
                    "name_suffix": None,
                    "person_apps": "https://api.planningcenteronline.com/people/v2/people/34765191/person_apps",
                    "phone_numbers": "https://api.planningcenteronline.com/people/v2/people/34765191/phone_numbers",
                    "school": None,
                    "social_profiles": "https://api.planningcenteronline.com/people/v2/people/34765191/social_profiles",
                    "workflow_cards": "https://api.planningcenteronline.com/people/v2/people/34765191/workflow_cards",
                    "self": "https://api.planningcenteronline.com/people/v2/people/34765191"
                }
            },
            "included": [],
            "meta": {
                "can_include": [
                    "addresses",
                    "emails",
                    "field_data",
                    "households",
                    "inactive_reason",
                    "marital_status",
                    "name_prefix",
                    "name_suffix",
                    "person_apps",
                    "phone_numbers",
                    "school",
                    "social_profiles"
                ],
                "parent": {
                    "id": "197716",
                    "type": "Organization"
                }
            }
        }

        result = people.people.get_by_url("https://api.planningcenteronline.com/people/v2/people/34765191")

        mock_people_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/people/34765191"
        )

        self.assertIsInstance(result, Person)
        self.assertEqual(result.first_name, 'Pico')
        self.assertEqual(result.last_name, 'Robot')

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    def test_list_by_url(self, mock_people_request):
        """Test getting lists of associations directly by URL."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        # Mock a page of results
        mock_people_request.return_value = {
            "links": {
                "self": "https://api.planningcenteronline.com/people/v2/people/34765191/emails"
            },
            "data": [
                {
                    "type": "Email",
                    "id": "23698235",
                    "attributes": {
                        "address": "pico@notarealaddress.com",
                        "created_at": "2018-02-21T19:34:29Z",
                        "location": "Home",
                        "primary": False,
                        "updated_at": "2018-02-21T19:34:29Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/emails/23698235"
                    },
                    "relationships": {
                        "person": {
                            "data": {
                                "type": "Person",
                                "id": "34765191"
                            }
                        }
                    }
                },
                {
                    "type": "Email",
                    "id": "23698245",
                    "attributes": {
                        "address": "pico2@notarealaddress.com",
                        "created_at": "2018-02-21T19:34:29Z",
                        "location": "Home",
                        "primary": False,
                        "updated_at": "2018-02-21T19:34:29Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/emails/23698245"
                    },
                    "relationships": {
                        "person": {
                            "data": {
                                "type": "Person",
                                "id": "34765191"
                            }
                        }
                    }
                }
            ],
            "included": [],
            "meta": {
                "total_count": 4,
                "count": 2,
                "can_order_by": [
                    "address",
                    "location",
                    "primary",
                    "created_at",
                    "updated_at"
                ],
                "can_query_by": [
                    "address",
                    "location",
                    "primary"
                ],
                "parent": {
                    "id": "34765191",
                    "type": "Person"
                }
            }
        }

        results = [result for result in people.people.list_by_url("https://api.planningcenteronline.com/people/v2/people/34765191/emails")]

        for result in results:
            self.assertIsInstance(result, Email)

        self.assertEqual(results[0].address, 'pico@notarealaddress.com')
        self.assertEqual(results[1].address, 'pico2@notarealaddress.com')
        self.assertEqual(len(results), 2)

    @patch('pypco.endpoints.people.People.dispatch_single_request')
    def test_create(self, mock_people_request):
        """Test creating new objects against the PCO APi."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        mock_people_request.return_value = {
            "data": {
                "type": "Person",
                "id": "34923107",
                "attributes": {
                    "anniversary": None,
                    "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_boy_gray.svg",
                    "birthdate": None,
                    "child": True,
                    "created_at": "2018-02-24T15:43:22Z",
                    "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_boy_gray.svg",
                    "first_name": "George",
                    "gender": "M",
                    "given_name": None,
                    "grade": None,
                    "graduation_year": None,
                    "inactivated_at": None,
                    "last_name": "Washington",
                    "medical_notes": None,
                    "membership": None,
                    "middle_name": None,
                    "name": "George Washington",
                    "nickname": None,
                    "people_permissions": None,
                    "remote_id": None,
                    "school_type": None,
                    "site_administrator": False,
                    "status": "active",
                    "updated_at": "2018-02-24T15:43:22Z"
                },
                "links": {
                    "addresses": "https://api.planningcenteronline.com/people/v2/people/34923107/addresses",
                    "apps": "https://api.planningcenteronline.com/people/v2/people/34923107/apps",
                    "connected_people": "https://api.planningcenteronline.com/people/v2/people/34923107/connected_people",
                    "emails": "https://api.planningcenteronline.com/people/v2/people/34923107/emails",
                    "field_data": "https://api.planningcenteronline.com/people/v2/people/34923107/field_data",
                    "household_memberships": "https://api.planningcenteronline.com/people/v2/people/34923107/household_memberships",
                    "households": "https://api.planningcenteronline.com/people/v2/people/34923107/households",
                    "inactive_reason": None,
                    "marital_status": None,
                    "message_groups": "https://api.planningcenteronline.com/people/v2/people/34923107/message_groups",
                    "messages": "https://api.planningcenteronline.com/people/v2/people/34923107/messages",
                    "name_prefix": None,
                    "name_suffix": None,
                    "notes": "https://api.planningcenteronline.com/people/v2/people/34923107/notes",
                    "person_apps": "https://api.planningcenteronline.com/people/v2/people/34923107/person_apps",
                    "phone_numbers": "https://api.planningcenteronline.com/people/v2/people/34923107/phone_numbers",
                    "school": None,
                    "social_profiles": "https://api.planningcenteronline.com/people/v2/people/34923107/social_profiles",
                    "workflow_cards": "https://api.planningcenteronline.com/people/v2/people/34923107/workflow_cards",
                    "self": "https://api.planningcenteronline.com/people/v2/people/34923107"
                }
            },
            "included": [],
            "meta": {
                "can_include": [
                    "addresses",
                    "emails",
                    "field_data",
                    "households",
                    "inactive_reason",
                    "marital_status",
                    "name_prefix",
                    "name_suffix",
                    "person_apps",
                    "phone_numbers",
                    "school",
                    "social_profiles"
                ],
                "parent": {
                    "id": "197716",
                    "type": "Organization"
                }
            }
        }

        new_person_dict = {
            "data": {
                "type": "Person",
                "attributes": {
                    "gender": "Male",
                    "child": True,
                    "first_name": "George",
                    "last_name": "Washington"
                }
            }
        }

        result = people.people.create(
            "https://api.planningcenteronline.com/people/v2/people/",
            new_person_dict
        )

        mock_people_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/people/",
            payload=new_person_dict,
            method=PCOAPIMethod.POST
        )

        self.assertEqual(result, mock_people_request.return_value)

    def test_get_parent_endpoint_name(self):
        """Test getting the parent endpoint name from subclasses."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        self.assertEqual(people.people.get_parent_endpoint_name(), "people")

    def get_pagination_mock(url, params=None, payload=None, method=PCOAPIMethod.GET): #pylint: disable=E0213
        """Create an object to mock pagination in API responses."""

        global OFFSET

        try:
            OFFSET
        except NameError:
            OFFSET = 0

        OFFSET += 3

        response = {
            "links": {
                "self": "https://api.planningcenteronline.com/people/v2/people?where[last_name]=Revere"
            },
            "data": [
                {
                    "type": "Person",
                    "id": "16555904",
                    "attributes": {
                        "anniversary": None,
                        "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                        "birthdate": "1916-01-01",
                        "child": False,
                        "created_at": "2016-04-23T01:19:54Z",
                        "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_man_gray.svg",
                        "first_name": "Paul",
                        "gender": "M",
                        "given_name": None,
                        "grade": None,
                        "graduation_year": None,
                        "inactivated_at": None,
                        "last_name": "Revere",
                        "medical_notes": None,
                        "membership": "Participant",
                        "middle_name": None,
                        "name": "Paul Revere",
                        "nickname": None,
                        "people_permissions": "Editor",
                        "remote_id": None,
                        "school_type": None,
                        "site_administrator": False,
                        "status": "active",
                        "updated_at": "2018-03-07T14:56:30Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/people/16555904"
                    }
                },
                {
                    "type": "Person",
                    "id": "25423946",
                    "attributes": {
                        "anniversary": None,
                        "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_boy_gray.svg",
                        "birthdate": None,
                        "child": True,
                        "created_at": "2017-04-11T22:42:08Z",
                        "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_boy_gray.svg",
                        "first_name": "Paul",
                        "gender": "M",
                        "given_name": None,
                        "grade": 4,
                        "graduation_year": None,
                        "inactivated_at": None,
                        "last_name": "Revere",
                        "medical_notes": None,
                        "membership": "Former Attender",
                        "middle_name": None,
                        "name": "Paul Revere Jr.",
                        "nickname": None,
                        "people_permissions": None,
                        "remote_id": None,
                        "school_type": "elementary",
                        "site_administrator": False,
                        "status": "active",
                        "updated_at": "2018-03-07T14:45:40Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/people/25423946"
                    }
                },
                {
                    "type": "Person",
                    "id": "25423947",
                    "attributes": {
                        "anniversary": None,
                        "avatar": "https://people.planningcenteronline.com/static/no_photo_thumbnail_woman_gray.svg",
                        "birthdate": None,
                        "child": False,
                        "created_at": "2017-04-11T22:42:09Z",
                        "demographic_avatar_url": "https://people.planningcenteronline.com/static/no_photo_thumbnail_woman_gray.svg",
                        "first_name": "Rachel",
                        "gender": "F",
                        "given_name": None,
                        "grade": None,
                        "graduation_year": None,
                        "inactivated_at": None,
                        "last_name": "Revere",
                        "medical_notes": None,
                        "membership": "Former Attender",
                        "middle_name": None,
                        "name": "Rachel Revere",
                        "nickname": None,
                        "people_permissions": None,
                        "remote_id": None,
                        "school_type": None,
                        "site_administrator": False,
                        "status": "active",
                        "updated_at": "2017-04-12T00:28:14Z"
                    },
                    "links": {
                        "self": "https://api.planningcenteronline.com/people/v2/people/25423947"
                    }
                }
            ],
            "included": [],
            "meta": {
                "total_count": 30,
                "count": 3,
                "next": {
                    "offset": OFFSET
                },
                "can_order_by": [
                    "given_name",
                    "first_name",
                    "nickname",
                    "middle_name",
                    "last_name",
                    "birthdate",
                    "anniversary",
                    "gender",
                    "grade",
                    "child",
                    "status",
                    "school_type",
                    "graduation_year",
                    "site_administrator",
                    "people_permissions",
                    "membership",
                    "inactivated_at",
                    "remote_id",
                    "medical_notes",
                    "created_at",
                    "updated_at"
                ],
                "can_query_by": [
                    "given_name",
                    "first_name",
                    "nickname",
                    "middle_name",
                    "last_name",
                    "birthdate",
                    "anniversary",
                    "gender",
                    "grade",
                    "child",
                    "status",
                    "school_type",
                    "graduation_year",
                    "site_administrator",
                    "people_permissions",
                    "membership",
                    "inactivated_at",
                    "remote_id",
                    "medical_notes",
                    "created_at",
                    "updated_at",
                    "search_name",
                    "search_name_or_email",
                    "id"
                ],
                "can_include": [
                    "addresses",
                    "emails",
                    "field_data",
                    "households",
                    "inactive_reason",
                    "marital_status",
                    "name_prefix",
                    "name_suffix",
                    "person_apps",
                    "phone_numbers",
                    "platform_notifications",
                    "school",
                    "social_profiles"
                ],
                "can_filter": [
                    "created_since",
                    "admins",
                    "organization_admins"
                ],
                "parent": {
                    "id": "197716",
                    "type": "Organization"
                }
            }
        } 

        if OFFSET == 30:
            del response['meta']['next']

        return response

    @patch('pypco.endpoints.people.People.dispatch_single_request', side_effect=get_pagination_mock)
    def test_list_by_url_pagination(self, mock_people_request):
        """Test pagination in the endpoint's list function."""

        people = PeopleEndpoint(PCOAuthConfig("app_id", "app_secret"), None)

        [person for person in people.people.list()]

        # Ensure that our final call contains the expected offset
        mock_people_request.assert_called_with(
            "https://api.planningcenteronline.com/people/v2/people",
            params=[('offset', 27)]
        )
