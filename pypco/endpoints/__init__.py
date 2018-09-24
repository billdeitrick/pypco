"""The endpoints module."""

# Import endpoint classes here; this ensures they and their subclasses
# are initialized. There's probably a better way to do this.
import pypco.endpoints.people
import pypco.endpoints.services
import pypco.endpoints.check_ins
import pypco.endpoints.giving

from .utils import PCOAuthConfig, PCOAuthException, PCOAuthType
from .base_endpoint import BaseEndpoint
