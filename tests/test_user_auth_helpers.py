"""Test pypco utility methods."""

import unittest
from unittest import mock

from requests import HTTPError
from requests import ConnectionError as RequestsConnectionError
from requests import Timeout

import pypco
from pypco.exceptions import PCORequestException
from pypco.exceptions import PCORequestTimeoutException
from pypco.exceptions import PCOUnexpectedRequestException

def mock_oauth_response(*args, **kwargs): #pylint: disable=E0211
    """Provide mocking for an oauth request

    Read more about this technique for mocking HTTP requests here:
    https://stackoverflow.com/questions/15753390/python-mock-requests-and-the-response/28507806#28507806
    """

    class MockOAuthResponse:
        """Mocking class for OAuth response

            Args:
                json_data (dict): JSON data returned by the mocked API.
                status_code (int): The HTTP status code returned by the mocked API.
        """

        def __init__(self, json_data, status_code):

            self.json_data = json_data
            self.status_code = status_code
            self.text = '{"test_key": "test_value"}'

        def json(self):
            """Return our mock JSON data"""

            return self.json_data

        def raise_for_status(self):
            """Raise HTTP exception if status code >= 400."""

            if 400 <= self.status_code <= 500:
                raise HTTPError(
                    u'%s Client Error: %s for url: %s' % \
                        (
                            self.status_code,
                            'Unauthorized',
                            'https://api.planningcenteronline.com/oauth/token'
                        ),
                    response=self
                )

    # If we have this attrib, we're getting an access token
    if 'code' in kwargs.get('data'):
        if args[0] != "https://api.planningcenteronline.com/oauth/token":
            return MockOAuthResponse(None, 404)

        if kwargs.get('data')['code'] == 'good':
            return MockOAuthResponse(
                {
                    'access_token': '863300f2f093e8be25fdd7f40f218f4276ecf0b5814a558d899730fcee81e898', #pylint: disable=C0301
                    'token_type': 'bearer',
                    'expires_in': 7200,
                    'refresh_token': '63d68cb3d8a46eea1c842f5ba469b2940a88a657992f915206be1253a175b6ad', #pylint: disable=C0301
                    'scope': 'people',
                    'created_at': 1516054388
                },
                200
            )

        if kwargs.get('data')['code'] == 'bad':
            return MockOAuthResponse(
                {
                    'error': 'invalid_client',
                    'error_description': 'Client authentication failed due to unknown client, no client authentication included, or unsupported authentication method.' #pylint: disable=C0301
                },
                401
            )

        if kwargs.get('data')['code'] == 'server_error':
            return MockOAuthResponse(
                {},
                500
            )

        if kwargs.get('data')['code'] == 'timeout':
            raise Timeout()

        if kwargs.get('data')['code'] == 'connection':
            raise RequestsConnectionError()

    # If we have this attrib, we're attempting a refresh
    if 'refresh_token' in kwargs.get('data'):
        if kwargs.get('data')['refresh_token'] == 'refresh_good':
            return MockOAuthResponse(
                {
                    'access_token': '863300f2f093e8be25fdd7f40f218f4276ecf0b5814a558d899730fcee81e898', #pylint: disable=C0301
                    'token_type': 'bearer',
                    'expires_in': 7200,
                    'refresh_token': '63d68cb3d8a46eea1c842f5ba469b2940a88a657992f915206be1253a175b6ad', #pylint: disable=C0301
                    'created_at': 1516054388
                },
                200
            )

        if kwargs.get('data')['refresh_token'] == 'refresh_bad':
            return MockOAuthResponse(
                {
                    'error': 'invalid_request',
                    'error_description': 'The refresh token is no longer valid'
                },
                401
            )

    return MockOAuthResponse(None, 400)

class TestGetBrowserRedirectUrl(unittest.TestCase):
    """Test pypco functionality for getting browser redirect URL."""

    def test_valid_url_single_scope(self):
        """Test the get_browser_redirect_url function with one OAUTH scope."""

        redirect_url = pypco.get_browser_redirect_url(
            'abc123',
            'https://nowhere.com?someurl',
            ['people']
        )

        self.assertEqual(
            "https://api.planningcenteronline.com/oauth/authorize?"
            "client_id=abc123&redirect_uri=https%3A%2F%2Fnowhere.com%3Fsomeurl&"
            "response_type=code&scope=people",
            redirect_url
        )

    def test_valid_url_multiple_scopes(self):
        """Test the get_browser_redirect_url function with multiple OAUTH scopes."""

        redirect_url = pypco.get_browser_redirect_url(
            'abc123',
            'https://nowhere.com?someurl',
            ['people', 'giving']
        )

        self.assertEqual(
            "https://api.planningcenteronline.com/oauth/authorize?"
            "client_id=abc123&redirect_uri=https%3A%2F%2Fnowhere.com%3Fsomeurl&"
            "response_type=code&scope=people+giving",
            redirect_url
        )

class TestDoOAUTHPost(unittest.TestCase):
    """Test the internal _do_oauth_post function."""

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_oauth_general_errors(self, mock_post): #pylint: disable=unused-argument
        """Ensure error response with invalid status code"""

        # Request timeout
        with self.assertRaises(PCORequestTimeoutException):
            pypco.user_auth_helpers._do_oauth_post( #pylint: disable=protected-access
                'https://api.planningcenteronline.com/oauth/token',
                client_id='id',
                client_secret='secret',
                code='timeout',
                redirect_uri='https://www.site.com',
                grant_type='authorization_code'
            )

        # Request connection error
        with self.assertRaises(PCOUnexpectedRequestException):
            pypco.user_auth_helpers._do_oauth_post( #pylint: disable=protected-access
                'https://api.planningcenteronline.com/oauth/token',
                client_id='id',
                client_secret='secret',
                code='connection',
                redirect_uri='https://www.site.com',
                grant_type='authorization_code'
            )

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_http_errors(self, mock_post): #pylint: disable=unused-argument
        """Ensure error response with http errors."""

        # Incorrect code
        with self.assertRaises(PCORequestException):
            pypco.user_auth_helpers._do_oauth_post( #pylint: disable=protected-access
                'https://api.planningcenteronline.com/oauth/token',
                client_id='id',
                client_secret='secret',
                code='bad',
                redirect_uri='https://www.site.com',
                grant_type='authorization_code'
            )

        # Server error
        with self.assertRaises(PCORequestException):
            pypco.user_auth_helpers._do_oauth_post( #pylint: disable=protected-access
                'https://api.planningcenteronline.com/oauth/token',
                client_id='id',
                client_secret='secret',
                code='server_error',
                redirect_uri='https://www.site.com',
                grant_type='authorization_code'
            )

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_successful_post(self, mock_post): #pylint: disable=unused-argument
        """Ensure successful post request execution with correct parameters."""

        response = pypco.user_auth_helpers._do_oauth_post( #pylint: disable=protected-access
            'https://api.planningcenteronline.com/oauth/token',
            client_id='id',
            client_secret='secret',
            code='good',
            redirect_uri='https://www.site.com',
            grant_type='authorization_code'
        )

        self.assertEqual(200, response.status_code)

        mock_post.assert_called_once_with(
            'https://api.planningcenteronline.com/oauth/token',
            data={
                'client_id': 'id',
                'client_secret': 'secret',
                'code': 'good',
                'redirect_uri': 'https://www.site.com',
                'grant_type': 'authorization_code'
            },
            headers={
                'User-Agent': 'pypco'
            },
            timeout=30
        )

class TestGetOAuthAccessToken(unittest.TestCase):
    """Test pypco functionality for getting oauth access tokens"""

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_valid_creds(self, mock_post): #pylint: disable=W0613
        """Ensure we can authenticate successfully with valid creds."""

        self.assertIn(
            'access_token',
            list(
                pypco.get_oauth_access_token(
                    'id',
                    'secret',
                    'good',
                    'https://www.site.com/').keys()
            )
        )

        mock_post.assert_called_once_with(
            'https://api.planningcenteronline.com/oauth/token',
            data={
                'client_id': 'id',
                'client_secret': 'secret',
                'code': 'good',
                'redirect_uri': 'https://www.site.com/',
                'grant_type': 'authorization_code'
            },
            headers={
                'User-Agent': 'pypco'
            },
            timeout=30
        )

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_invalid_code(self, mock_post): #pylint: disable=W0613
        """Ensure error response with invalid status code"""

        with self.assertRaises(PCORequestException) as err_cm:
            pypco.get_oauth_access_token(
                'id',
                'secret',
                'bad',
                'https://www.site.com/'
            )

        self.assertEqual(401, err_cm.exception.status_code)
        self.assertEqual('{"test_key": "test_value"}', err_cm.exception.response_body)

        mock_post.assert_called_once_with(
            'https://api.planningcenteronline.com/oauth/token',
            data={
                'client_id': 'id',
                'client_secret': 'secret',
                'code': 'bad',
                'redirect_uri': 'https://www.site.com/',
                'grant_type': 'authorization_code'
            },
            headers={
                'User-Agent': 'pypco'
            },
            timeout=30
        )

class TestGetOAuthRefreshToken(unittest.TestCase):
    """Test pypco functionality for getting oauth refresh tokens"""

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_valid_refresh_token(self, mock_post):
        """Verify successful refresh with valid token."""

        self.assertIn(
            'access_token',
            list(
                pypco.get_oauth_refresh_token(
                    'id',
                    'secret',
                    'refresh_good'
                ).keys()
            )
        )

        mock_post.assert_called_once_with(
            'https://api.planningcenteronline.com/oauth/token',
            data={
                'client_id': 'id',
                'client_secret': 'secret',
                'refresh_token': 'refresh_good',
                'grant_type': 'refresh_token'
            },
            headers={
                'User-Agent': 'pypco'
            },
            timeout=30
        )

    @mock.patch('requests.post', side_effect=mock_oauth_response)
    def test_invalid_refresh_token(self, mock_post):
        """Verify refresh fails with invalid token."""

        with self.assertRaises(PCORequestException) as err_cm:
            pypco.get_oauth_refresh_token(
                'id',
                'secret',
                'refresh_bad'
            ).keys()

        self.assertEqual(401, err_cm.exception.status_code)
        self.assertEqual('{"test_key": "test_value"}', err_cm.exception.response_body)

        mock_post.assert_called_once_with(
            'https://api.planningcenteronline.com/oauth/token',
            data={
                'client_id': 'id',
                'client_secret': 'secret',
                'refresh_token': 'refresh_bad',
                'grant_type': 'refresh_token'
            },
            headers={
                'User-Agent': 'pypco'
            },
            timeout=30
        )
