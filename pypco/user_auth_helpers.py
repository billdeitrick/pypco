"""User-facing authentication helper functions for pypco."""

import urllib
import requests

from .exceptions import PCORequestException

def get_browser_redirect_url(client_id, redirect_uri, scopes):
    """Get the URL to which the user's browser should be redirected.

    This helps you perform step 1 of PCO OAUTH as described at:
    https://developer.planning.center/docs/#/introduction/authentication

    Args:
        client_id (str): The client id for your app.
        redirect_uri (str): The redirect URI, identical to what was used in step 1.
        scopes (list): A list of the scopes to which you will authenticate (see above).

    Returns:
        (str): The url to which a user's browser should be directed for OAUTH.
    """

    url = "https://api.planningcenteronline.com/oauth/authorize?"

    params = [
        ('client_id', client_id),
        ('redirect_uri', redirect_uri),
        ('response_type', 'code'),
        ('scope', ' '.join(scopes))
    ]

    return "{}{}".format(url, urllib.parse.urlencode(params))

def get_oauth_access_token(client_id, client_secret, code, redirect_uri):
    """Get the access token for the client.

    This assumes you have already completed steps 1 and 2 as described at:
    https://developer.planning.center/docs/#/introduction/authentication

    Args:
        client_id (str): The client id for your app.
        client_secret (str): The client secret for your app.
        code (int): The code returned by step one of your OAUTH sequence.
        redirect_uri (str): The redirect URI, identical to what was used in step 1.

    Returns:
        (requests.response): The PCO response to your OAUTH request.
    """

    response = requests.post(
        "https://api.planningcenteronline.com/oauth/token",
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': "authorization_code"
        },
        headers={
            'User-Agent': 'pypco'
        },
        timeout=30
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as err:
        raise PCORequestException(
            response.status_code,
            str(err),
            response_body=response.text
        ) from err

    return response.json()

# TODO: Add function to get refresh token
