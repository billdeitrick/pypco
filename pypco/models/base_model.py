"""Provides the base model object from which all other models inherit.
"""

import copy

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
        self._update_attribs = []
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

        search_dicts = [
            self._data,
            self._data['attributes']
        ]

        for search_dict in search_dicts:
            if name in search_dict.keys():
                return search_dict[name]

        raise AttributeError("'{}' is not an available attribute on this object.".format(name))

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
            self._update_attribs.append(name)

    def delete(self):
        """Delete this object.

        WARNING: This is most likely permanent. Make sure you're REALLY
        sure you want to delete this object on PCO before calling this function.

        Raises:
            PCOModelStateError: Raised if the state of the current object is invalid
            for this function call (i.e., you cannot delete an object that hasn't been
            pulled from PCO at some point during its lifecycle.)
        """

        if self._user_created == True or not self._data or not 'id' in self._data:
            raise PCOModelStateError("Couldn't delete this object; it appears it was never synced with PCO.")

        self._endpoint.delete(self.links['self'])

    def update(self):
        """Update any changes you've made to the current object in PCO.

        Raises:
            PCOModelStateError: Raised if the state of the current object is invalid
            for this function call. This would be the case if the current object has
            never been connected PCO (i.e., one you create new but never actually created
            on the PCO API via the create function).
        """

        if self._user_created == True or not self._data or not 'id' in self._data:
            raise PCOModelStateError("Couldn't delete this object; it appears it was never synced with PCO.")

        self._data = self._endpoint.update(self.links['self'], self._get_updates())['data']

        self._update_attribs = []

    def refresh(self):
        """Refresh the current object with data from the PCO API."""

        refr_obj = self._endpoint.get_by_url(self.links['self'])

        self._data = refr_obj.data

    def _get_updates(self):
        """Get updated attributes to be pushed to PCO.

        Returns:
            A dictionary representing only the changed attributes to be pushed to PCO.
        """

        return {
            'data': {
                'type': self.type,
                'id': self.id,
                'attributes': {key:self._data['attributes'][key] for key in self._update_attribs}
            }
        }        

    @property
    def data(self):
        """Get a copy of this object's raw data structure.
        
        Returns:
            A copy of the dict object that stores this object's raw data from
            the PCO API.
        """
        
        return copy.deepcopy(self._data)

    # TODO: Build capability for user to create new objects

    # TODO: Build the capability to manage link attributes (link_manager object?)
    # TODO: Build capability to access data in the relationships attribute

    # TODO: Build a json function to convert the object to JSON
    # TODO: Build the capability to create models from JSON

    # TODO: Handle OrganizationStatistics weirdness (or ignore for now?)

class PCOModelStateError(Exception):
    """An exception representing a function call against a model that is
    in an invalid state."""

    pass