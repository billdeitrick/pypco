"""Models for PCO people.

To add additional models, simply add additional classes
subclassing the PeopleModel class.
"""

#pylint: disable=C0321,R0903,C0111

from .base_model import BaseModel

# The base people model
class PeopleModel(BaseModel): pass

# People models
class Address(PeopleModel): pass
class App(PeopleModel): pass
class Campus(PeopleModel): pass
class Carrier(PeopleModel): pass
class Condition(PeopleModel): pass
class ConnectedPerson(PeopleModel): pass
class Email(PeopleModel): pass
class FieldDatum(PeopleModel): pass
class FieldDefinition(PeopleModel): pass
class FieldOption(PeopleModel): pass
class Household(PeopleModel): pass
class HouseholdMembership(PeopleModel): pass
class InactiveReason(PeopleModel): pass
class List(PeopleModel): pass
class ListShare(PeopleModel): pass
class MailchimpSyncStatus(PeopleModel): pass
class MaritalStatus(PeopleModel): pass
class Message(PeopleModel): pass
class MessageGroup(PeopleModel): pass
class NamePrefix(PeopleModel): pass
class NameSuffix(PeopleModel): pass
class Organization(PeopleModel): pass
class PeopleImport(PeopleModel): pass
class PeopleImportConflict(PeopleModel): pass
class PeopleImportHistory(PeopleModel): pass
class Person(PeopleModel): pass
class PersonApp(PeopleModel): pass
class PersonMerger(PeopleModel): pass
class PhoneNumber(PeopleModel): pass
class Report(PeopleModel): pass
class Rule(PeopleModel): pass
class SchoolOption(PeopleModel): pass
class SocialProfile(PeopleModel): pass
class Tab(PeopleModel): pass
class Workflow(PeopleModel): pass
class WorkflowCard(PeopleModel): pass
class WorkflowCardActivity(PeopleModel): pass
class WorkflowCardNote(PeopleModel): pass
class WorkflowShare(PeopleModel): pass
class WorkflowStep(PeopleModel): pass
class WorkflowStepAssigneeSummary(PeopleModel): pass
