"""Module containing the main PCO object for the PCO API wrapper."""

import logging
from .endpoints import PCOAuthConfig, BaseEndpoint

class PCO(object):
    """The entry point to the PCO API.

    Attributes:
        auth_config (PCOAuthConfig): The authentication configuration for this instance.
    """

    def __init__(self, application_id=None, secret=None, token=None):
        """Initialize the PCO entry point.

        Note:
            You must specify either an application ID and a secret or an oauth token.
            If you specify an invalid combination of these arguments, an exception will be
            raised when you attempt to make API calls.
        """

        self._log = logging.getLogger(__name__)
        self._log.info("Initializing the PCO wrapper.")

        self.auth_config = PCOAuthConfig(application_id, secret, token)
        self._log.debug("Initialized the auth_config object.")

        for klass in BaseEndpoint.__subclasses__():
            setattr(self, klass.resolve_root_endpoint_name(), klass(self.auth_config))

    # TODO: write "new" function that takes the model class as arg, returns new user-created object of that type
    # From a user perspective, this looks like: new_guy = pco.new(pypco.models.people.Person)
