"""Internal authentication helper objects for pypco."""

import base64
from enum import Enum, auto

from typing import Optional

from pypco.user_auth_helpers import get_cc_org_token
from .exceptions import PCOCredentialsException


class PCOAuthType(Enum):  # pylint: disable=R0903
    """Defines PCO authentication types."""

    PAT = auto()
    OAUTH = auto()
    ORGTOKEN = auto()


class PCOAuthConfig:
    """Auth configuration for PCO.

        Args:
            application_id (str): The application ID for your application (PAT).
            secret (str): The secret for your application (PAT).
            token (str): The token for your application (OAUTH).
            cc_name (str): The vanity name portion of the <vanity_name>.churchcenter.com url
            auth_type (PCOAuthType): The authentication type specified by this config object.
    """

    def __init__(
            self,
            application_id: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            secret: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            token: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            cc_name: Optional[str] = None  # pylint: disable=unsubscriptable-object
    ):

        self.application_id = application_id
        self.secret = secret
        self.token = token
        self.cc_name = cc_name

    @property
    def auth_type(self) -> PCOAuthType:
        """The authentication type specified by this configuration.

        Raises:
            PCOCredentialsException: You have specified invalid authentication information.

        Returns:
            PCOAuthType: The authentication type for this config.
        """

        if self.application_id and self.secret and not (self.token or self.cc_name):  # pylint: disable=no-else-return
            return PCOAuthType.PAT
        elif self.token and not (self.application_id or self.secret or self.cc_name):
            return PCOAuthType.OAUTH
        elif self.cc_name and not (self.application_id or self.secret or self.token):
            return PCOAuthType.ORGTOKEN
        else:
            raise PCOCredentialsException(
                "You have specified invalid authentication information. "
                "You must specify either an application id and a secret for "
                "your Personal Access Token (PAT) or an OAuth token."
            )

    @property
    def auth_header(self) -> str:
        """Get the authorization header for this authentication configuration scheme.

        Returns:
            str: The authorization header text to pass as a request header.
        """

        # If PAT, use Basic auth
        if self.auth_type == PCOAuthType.PAT:
            return "Basic " \
                   f"{base64.b64encode(f'{self.application_id}:{self.secret}'.encode()).decode()}"

        if self.auth_type == PCOAuthType.ORGTOKEN:
            return f"OrganizationToken {get_cc_org_token(self.cc_name)}"

        # Otherwise OAUTH using the Bearer scheme
        return f"Bearer {self.token}"
