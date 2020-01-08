# Pypco ReadMe

[![Build Status](https://travis-ci.org/billdeitrick/pypco.svg?branch=master)](https://travis-ci.org/billdeitrick/pypco) [![codecov](https://codecov.io/gh/billdeitrick/pypco/branch/master/graph/badge.svg)](https://codecov.io/gh/billdeitrick/pypco) [![Documentation Status](https://readthedocs.org/projects/pypco/badge/?version=latest)](https://pypco.readthedocs.io/en/latest/?badge=latest)

Stop writing boilerplate code to communicate with the [Planning Center Online](https://planning.center) REST API, and start using pypco! Pypco is a Python wrapper library that supports the full breadth of the PCO REST API. With pypco, you'll spend less time worrying about building and managing HTTP requests and more time building cool things.

[>>> Read the Docs <<<](https://readthedocs.org/projects/pypco/badge/?version=latest) 

## Features

* *Boilerplate Done for You:* No need to manage HTTP requests, and useful helper functions included (authentication, iteration/pagination, new object templating, etc.)! With pypco, you can do stuff like this:
```python
import pypco
pco = pypco.PCO("<app_id>", "<app_secret>")

# Print first and last names of everyone in People
for person in pco.iterate('/people/v2/people'):
    print(f'{person["data"]["attributes"]["first_name"]} '\
    f'{person["data"]["attributes"]["last_name"]}')

# Create, save, and print a new person's attribs
payload = pco.template(
  'Person',
  {'first_name': 'John', 'last_name': 'Doe'}
)
new_person = pco.post('/people/v2/people', payload)
print(new_person['data']['attributes'])

# Change our new person's last name and print attribs
payload = pco.template(
  'Person',
  {'last_name': 'Smith'}
)
updated_person = pco.patch(
  f'/people/v2/people/{new_person["data"]["id"]}',
  payload
)
print(updated_person['data']['attributes'])

# Add an email address for our person
payload = pco.template(
  'Email',
  {
    'address': 'john.doe@mailinator.com',
    'location': 'Home'
  }
)
email_object = pco.post(
  f'/people/v2/people/{updated_person["data"]["id"]}/emails',
  payload
)

# Iterate through our person's email addresses
for email in pco.iterate(
  f'/people/v2/people/{updated_person["data"]["id"]}/emails'
):
  print(email['data']['attributes']['address'])
  
```
* *Automatic rate limit handling:* If you hit your rate limit, pypco will automatically pause requests and continue once your rate limit period has expired.
* *Simple Wrapper API:* Using API wrappers can feel like learning *two* new APIs: the REST API itself and the wrapper you're using. Pypco's simple approach is built around the HTTP verbs you already know: GET, POST, PATCH, and DELETE. As a result, after a few minutes with the pypco docs you'll be spending your time in the PCO API docs instead and be on your way to getting things done.
* *Full API Support:* Pypco supports all versions of the PCO v2 REST API, and supports any combination of API versions you might use for each of the PCO apps.

## Version 1.0

Code written for pypco v0 will not be compatible with the v1 release. Because of changes in the PCO API (primarily the introduction of versioning) and the need for significantly improved performance, v1 is almost a complete rewrite. The result is a much more flexible, performant, robust, and efficient API wrapper. Though perhaps a bit less "pythonic", pypco v1.0.x will be much more maintainable going forward. 

If you're relying on pypco v0, the pypco-legacy package is available for you on PyPi. No new features will be added to the v0 release, but bug fixes may be considered and released. Open an issue and plead your case. 🙂

## License

Pypco is licensed under the terms of the MIT License.