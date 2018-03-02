# Pypco ReadME

[![Build Status](https://travis-ci.org/billdeitrick/pypco.svg?branch=master)](https://travis-ci.org/billdeitrick/pypco) [![codecov](https://codecov.io/gh/billdeitrick/pypco/branch/master/graph/badge.svg)](https://codecov.io/gh/billdeitrick/pypco)


Pypco an object-oriented, Pythonic client for the [Planning Center Online](https://planning.center) API. The library is currently in very active development and not yet recommended for production use (but hopefully will be ready soon!).

## Features

* *Object-oriented, Pythonic interface:* No writing URLS or building/managing HTTP requests! With pypco, you can do stuff like this:
```python
import pypco
pco = pypco.PCO("<app_id>", "<app_secret>")

# Rename everyone in your PCO people account to "John Doe"
# You probably shouldn't *actually* do this...
for person in pco.people.people.list():
    person.first_name = "John"
    person.last_name = "Doe"
    person.update()

# Create and save a new person
new_person = pco.new(pypco.models.people.Person)
new_person.first_name = "John"
new_person.last_name = "Doe"
new_person.update()

# Get the person with ID 123, and view their first name
person = pco.people.people.get("123")
print(person.first_name)

# Get the persion with ID 123 and iterate through their addresses
person = pco.people.people.get("1234")
for address in person.rel.addresses.list():
    print(address)
```
* *Automatic rate limiting handling:* If your application is rate limited, pypco will automatically delay your requests until your rate limit period has expired.
* *REST API parity:* Pypco aims to be simple to use. After a quick read of the quickstart guide (coming soon), you should be able to use pypco simply by reading the PCO API docs. No sense in reinventing the wheel and/or overcomplicating things.

## License

Pypco is licensed under the terms of the MIT License.