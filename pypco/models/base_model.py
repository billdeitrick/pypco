"""Provides the base model object from which all other models inherit.
"""

class BaseModel():
    """Base model class from which all models inherit."""

    def __init__(self, endpoint, data=None, user_created=False, from_get=False):
        """Initialize the model class.

        Args:
            endpoint (BaseEndpoint): The endpoint associated with this object.
            data (dict): The dict from which to build object properties.
            user_created (boolean): Was this model created by a user?
            get (boolean): Was this model created by a direct get request?
        """

        self._endpoint = endpoint
        self._data = data
        self._user_created = user_created
        self._from_get = from_get

    # TODO: Build the capability to manage links/relationships (link_manager object?)

    # TODO: Build the capability to create new objects
    # TODO: Build the capability to update existing objects
    # TODO: Build the capability to delete objects

    # TODO: Build a json function to convert the object to JSON
    # TODO: Build the capability to create models from JSON

    # TODO: Handle OrganizationStatistics weirdness
