"""Internal authentication helper objects for pypco."""

import base64
from enum import Enum, auto

from .exceptions import PCOCredentialsException

class PCOAuthConfig:
    """Auth configuration for PCO.

        Args:
            application_id (str): The application ID for your application (PAT).
            secret (str): The secret for your application (PAT).
            token (str): The token for your application (OAUTH).
            org_token: The OrganizationToken used for api.churchcenter.com
            auth_type (PCOAuthType): The authentiation type specified by this config object.
    """

    def __init__(self, application_id=None, secret=None, token=None, org_token=None):

        self.application_id = application_id
        self.secret = secret
        self.token = token
        self.org_token = org_token

    @property
    def auth_type(self):
        """The authentication type specified by this configuration.

        Raises:
            PCOCredentialsException: You have specified invalid authentication information.

        Returns:
            PCOAuthType: The authentication type for this config.
        """

        if self.application_id and self.secret and not (self.token or self.org_token): #pylint: disable=no-else-return
            return PCOAuthType.PAT
        elif self.token and not (self.application_id or self.secret or self.org_token):
            return PCOAuthType.OAUTH
        elif self.org_token and not (self.application_id or self.secret or self.token):
            return PCOAuthType.ORGTOKEN
        else:
            raise PCOCredentialsException(
                "You have specified invalid authentication information. "
                "You must specify either an application id and a secret for "
                "your Personal Access Token (PAT) or an OAuth token."
            )

    @property
    def auth_header(self):
        """Get the authorization header for this authentication configuration scheme.

        Returns:
            str: The authorization header text to pass as a request header.
        """

        # If PAT, use Basic auth
        if self.auth_type == PCOAuthType.PAT:
            return "Basic {}".format(
                base64.b64encode(
                    '{}:{}'.format(
                        self.application_id,
                        self.secret
                    ).encode()
                ).decode()
            )
        if self.auth_type == PCOAuthType.ORGTOKEN:
            return "OrganizationToken {}".format(self.org_token)

        # Otherwise OAUTH using the Bearer scheme
        return "Bearer {}".format(self.token)

class PCOAuthType(Enum): #pylint: disable=R0903
    """Defines PCO authentication types."""

    PAT = auto()
    OAUTH = auto()
    ORGTOKEN = auto()
