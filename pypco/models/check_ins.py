"""Models for PCO check ins.

To add additional models, simply add additional classes
subclassing the CheckInsModel class.
"""

#pylint: disable=C0321,R0903,C0111

from .base_model import BaseModel

# The base check ins model
class CheckInsModel(BaseModel): pass

# Check ins models
class AttendanceType(CheckInsModel): ENDPOINT_NAME='events'
class CheckIn(CheckInsModel): ENDPOINT_NAME='check_ins'
class CheckInGroup(CheckInsModel): ENDPOINT_NAME='check_ins'
class Event(CheckInsModel): ENDPOINT_NAME='events'
class EventLabel(CheckInsModel): ENDPOINT_NAME='events'
class EventPeriod(CheckInsModel): ENDPOINT_NAME='check_ins'
class EventTime(CheckInsModel): ENDPOINT_NAME='event_times'
class Headcount(CheckInsModel): ENDPOINT_NAME='headcounts'
class Label(CheckInsModel): ENDPOINT_NAME='labels'
class Location(CheckInsModel): ENDPOINT_NAME='check_ins'
class LocationEventPeriod(CheckInsModel): ENDPOINT_NAME='check_ins'
class LocationEventTime(CheckInsModel): ENDPOINT_NAME='event_times'
class LocationLabel(CheckInsModel): ENDPOINT_NAME='labels'
class Option(CheckInsModel): ENDPOINT_NAME='check_ins'
class Organization(CheckInsModel): ENDPOINT_NAME=''
class Pass(CheckInsModel): ENDPOINT_NAME='passes'
class Person(CheckInsModel): ENDPOINT_NAME='people'
class PersonEvent(CheckInsModel): ENDPOINT_NAME='events'
class Station(CheckInsModel): ENDPOINT_NAME='stations'
class Theme(CheckInsModel): ENDPOINT_NAME='themes'
