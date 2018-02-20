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
        self._link_managers = None
        self._user_created = user_created
        self._from_get = from_get

    def __getattr__(self, name):
        """Magic method to dynamically get object properties.
        
        Model attributes are dynamically available based on the data returned by the PCO API.
        To determine what attributes are/aren't available, check the PCO API docs.

        Args:
            name (str): The attribute name

        Returns:
            The attribute value as a string.

        Raises:
            AttributeError: Thrown if the property does not exist on the object.
        """

        value = None

        search_dicts = [
            self._data,
            self._data['attributes']
        ]

        for search_dict in search_dicts:
            if name in search_dict.keys():
                value = search_dict[name]

        if not value:
            raise AttributeError("'{}' is not an available attribute on this object.".format(name))

        return value

    def __setattr__(self, name, value):
        """Magic method to facilitate handling object properties.

        If the attribute name begins with an underscore (a "private" variable),
        we go ahead and set it on the object. If it does not begin with an underscore,
        we set it in the attributes dict of the model's data dictionary. We don't
        do any validation on attributes that are set; we'll let the PCO API do
        this for us.

        Args:
            name (str): The name of the attribute to set.
            value (object):  The value to set for the specified attribute.
        """

        if name[0] == '_':
            object.__setattr__(self, name, value)
        else:
            self._data['attributes'][name] = value

    # TODO: Build the capability to manage link attributes (link_manager object?)
    # TODO: Build capability to access data in the relationships attribute

    # TODO: Build capability for user to create new objects
    # TODO: Build the capability to update existing objects (a "save" function?)
    # TODO: Build the capability to delete objects (a "delete" function?)

    # TODO: Build a json function to convert the object to JSON
    # TODO: Build the capability to create models from JSON

    # TODO: Handle OrganizationStatistics weirdness
