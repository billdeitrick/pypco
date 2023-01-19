"""User-facing authentication helper functions for pypco."""

import urllib
from typing import List, Optional
from json import JSONDecodeError

import requests

from .exceptions import PCORequestException
from .exceptions import PCORequestTimeoutException
from .exceptions import PCOUnexpectedRequestException


def get_browser_redirect_url(client_id: str, redirect_uri: str, scopes: List[str]) -> str:
    """Get the URL to which the user's browser should be redirected.

    This helps you perform step 1 of PCO OAUTH as described at:
    https://developer.planning.center/docs/#/introduction/authentication

    Args:
        client_id (str): The client id for your app.
        redirect_uri (str): The redirect URI.
        scopes (list): A list of the scopes to which you will authenticate (see above).

    Returns:
        str: The url to which a user's browser should be directed for OAUTH.
    """

    url = "https://api.planningcenteronline.com/oauth/authorize?"

    params = [
        ('client_id', client_id),
        ('redirect_uri', redirect_uri),
        ('response_type', 'code'),
        ('scope', ' '.join(scopes))
    ]

    return f"{url}{urllib.parse.urlencode(params)}"


def _do_oauth_post(url: str, **kwargs) -> requests.Response:
    """Do a Post request to facilitate the OAUTH process.

    Handles error handling appropriately and raises pypco exceptions.

    Args:
        url (str): The url to which the request should be made.
        **kwargs: Data fields sent as the request payload.

    Raises:
        PCORequestTimeoutException: The request timed out.
        PCOUnexpectedRequestException: Something unexpected went wrong with the request.
        PCORequestException: The HTTP response from PCO indicated an error.

    Returns:
        requests.Response: The response object from the request.
    """

    try:
        response = requests.post(
            url,
            data={
                **kwargs
            },
            headers={
                'User-Agent': 'pypco'
            },
            timeout=30
        )
    except requests.exceptions.Timeout as err:
        raise PCORequestTimeoutException() from err
    except Exception as err:
        raise PCOUnexpectedRequestException(str(err)) from err

    try:
        response.raise_for_status()
    except requests.HTTPError as err:
        raise PCORequestException(
            response.status_code,
            str(err),
            response_body=response.text
        ) from err

    return response


def get_oauth_access_token(client_id: str, client_secret: str, code: int, redirect_uri: str) -> dict:
    """Get the access token for the client.

    This assumes you have already completed steps 1 and 2 as described at:
    https://developer.planning.center/docs/#/introduction/authentication

    Args:
        client_id (str): The client id for your app.
        client_secret (str): The client secret for your app.
        code (int): The code returned by step one of your OAUTH sequence.
        redirect_uri (str): The redirect URI, identical to what was used in step 1.

    Raises:
        PCORequestTimeoutException: The request timed out.
        PCOUnexpectedRequestException: Something unexpected went wrong with the request.
        PCORequestException: The HTTP response from PCO indicated an error.

    Returns:
        dict: The PCO response to your OAUTH request.
    """

    return _do_oauth_post(
        'https://api.planningcenteronline.com/oauth/token',
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=redirect_uri,
        grant_type="authorization_code"
    ).json()


def get_oauth_refresh_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh the access token.

    This assumes you have already completed steps 1, 2, and 3 as described at:
    https://developer.planning.center/docs/#/introduction/authentication

    Args:
        client_id (str): The client id for your app.
        client_secret (str): The client secret for your app.
        refresh_token (str): The refresh token for the user.

    Raises:
        PCORequestTimeoutException: The request timed out.
        PCOUnexpectedRequestException: Something unexpected went wrong with the request.
        PCORequestException: The HTTP response from PCO indicated an error.

    Returns:
        dict: The PCO response to your token refresh request.
    """

    return _do_oauth_post(
        'https://api.planningcenteronline.com/oauth/token',
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        grant_type='refresh_token'
    ).json()


def get_cc_org_token(cc_name: Optional[str] = None) -> Optional[str]:  # pylint: disable=unsubscriptable-object
    """Get a non-authenticated Church Center OrganizationToken.

    Args:
        cc_name (str): The organization_name part of the organization_name.churchcenter.com url.

    Raises:

    Returns:
        str: String of organization token
    """
    try:
        response = requests.post(
            f'https://{cc_name}.churchcenter.com/sessions/tokens',
            timeout=30
        )

    except requests.exceptions.Timeout as err:
        raise PCORequestTimeoutException() from err
    except Exception as err:
        raise PCOUnexpectedRequestException(str(err)) from err

    try:
        response.raise_for_status()
    except requests.HTTPError as err:
        raise PCORequestException(
            response.status_code,
            str(err),
            response_body=response.text
        ) from err
    try:
        response.json()
        return str(response.json()['data']['attributes']['token'])
    except JSONDecodeError as err:
        raise PCOUnexpectedRequestException("Invalid Church Center URL") from err
