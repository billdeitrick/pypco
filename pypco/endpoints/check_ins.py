"""Endpoints for PCO Check Ins.

To add additional endpoints, simply add additional classes
subclassing the CheckInsEndpoint class.
"""

#pylint: disable=C0304,R0903,C0111,C0321

from .base_endpoint import BaseEndpoint

# The check ins endpoint
class CheckInsEndpoint(BaseEndpoint): pass

# All objects on the check ins endpoint
class CheckIns(CheckInsEndpoint): pass
class EventTimes(CheckInsEndpoint): pass
class Events(CheckInsEndpoint): pass
class Headcounts(CheckInsEndpoint): pass
class Labels(CheckInsEndpoint): pass
class Passes(CheckInsEndpoint): pass
class People(CheckInsEndpoint): pass
class Stations(CheckInsEndpoint): pass
class Themes(CheckInsEndpoint): pass
