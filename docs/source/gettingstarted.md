# Getting Started

## Introduction

Pypco is an object-oriented, Pythonic client providing a Python interface to the [Planning Center Online](https://planning.center) API. This means you can stop worrying about individual HTTP requests, formatting JSON, dealing with rate limiting, etc. Pypco takes handles all of this for you, and lets you quickly start working with your PCO data.

Below you'll find some brief information about pypco's design goals and features. If you're not interested, feel free to jump right to [installation](#installation).

### Design Goals

* **Ease of use:** Pypco is designed first and foremost to be easy and intuitive to use. If there's a choice between implementing some functionality in pypco the "easy way" and making pypco easier to use, always err on the side of making pypco easier to use.
* **Helpful abstraction:** Pypco aims to abstract away all of the boilerplate stuff you need to do when connecting to the PCO API. Spend your time getting stuff done instead of writing HTTP requests.
* **REST API Parity:** You shouldn't have to spend lots of time reading the pypco documentation to figure out how to do something. Once you learn the simple idioms pypco uses, you should spend most of your time directly in the PCO API docs and know exactly what pypco calls to make to get what you want.
* **Full REST API support:** Pypco aims to support all functionality available in the PCO REST API. This doesn't mean every possible call is supported--sometimes there are multiple ways of doing the same thing, or certain calls that aren't needed to accomplish some task. The goal is to provide at least one supported way to accomplish any task supported by the REST API.

### Features

* **Native Python:** Interact with the PCO API using Pythonic code. Pypco will build HTTP requests for you and let you manipulate objects from PCO as native Python objects.
* **Automatic rate limiting management:** Pypco automatically handles rate limiting. When your calls are rate limited, pypco will automatically slow down for you. This means that your application doesn't have to be concerned about rate limiting at all--just let pypco deal with it for you.
* **Full CRUD support:** Create, read, update, and delete objects as supported by the PCO API. 

## Installation

[`pip`](https://pypi.org/project/pip/) is the easiest way to install pypco. Run the single command below and you're done.

```bash
pip install pypco
```

The excellent [`pipenv`](https://pypi.org/project/pipenv/) from [Kenneth Reitz](https://github.com/kennethreitz) is also highly recommended. Assuming you already have pipenv installed, run the single command below and you're ready to go.

```bash
pipenv install pypco
```

Alternatively, if you want the bleeding edge or you want the source more readily available, you can install from [GitHub](https://github.com/billdeitrick/pypco).

Either clone the repository:

```bash
git clone git://github.com/billdeitrick/pypco.git
```

Or download a tarball:

```bash
curl -OL https://github.com/billdeitrick/pypco/tarball/master
```

You can also substitute "zipball" for "tarball" in the URL above to get a zip file instead.

Once you've extracted the code and have a shell in the extracted directory, you can install pypco to your Python's site-packages with:

```bash
python setup.py install
```

Alternatively, you could simply embed the pypco source directory in your own Python package.

Once you've gotten pypco installed, make sure you can import it in your Python script or at the interactive Python prompt with:

```python
import pypco
```

Once you can import the module, you're ready to go!

## Authentication

The PCO API offers two options for authentication: OAuth or Personal Access Tokens (hereafter referred to as PAT).  Typically, you would use PAT for applications that will access your own data (i.e. applications that you create and use yourself) and OAuth for applications that will access a third-party's data (i.e. applications you will package and make available for others to use.)

PCO provides much more detail about authentication in their [API Documentation](https://developer.planning.center/docs/#/introduction/authentication).

### Personal Access Token (PAT) Authentication

PAT authentication is the simplest method (and probably what you'll use if you're wanting to kick the tires), so we'll start with that. 

First, you'll need to generate your application id and secret. Sign into your account at [api.planningcenteronline.com](https://api.planningcenteronline.com/). Click **Applications** in the toolbar and then click **New Personal Access Token** under the Personal Access Tokens heading. Enter a description of your choosing, and ensure that the 2018-08-01 API version is selected for all apps (this is the only API version pypco supports as of this writing). Click **Submit**, and you'll see your generated token. 

Now, you're ready to connect to the PCO API. The example below demonstrates authentication with a PAT and executes a simple query to get and display single person from your account.

```python
import pypco

# Get an instance of the PCO object using your personal access token.
pco = pypco.PCO("<APPLICATION_ID_HERE>", "<APPLICATION_SECRET_HERE>")

# Get a single person from your account and display their information
# We'll call the People endpoint's list() function, which returns an iterator
people = pco.people.people.list()
person = next(people)
print(person)
```

If you can run the above example and see output for one of the people in your PCO account, you have successfully connected to the API. Continue to [API Tour](#apitour) to learn more.

### OAuth Authentication

OAuth is the more complex method for authenticating against PCO, but is what you'll want to use if you're building an app that will access a third-party's data. 

Before diving in, it's helpful to have an understanding of OAuth basics, both in general and as they apply to the PCO API specifically. You can learn more than you'll probably ever want to know about OAuth over at [oauth.net](<https://oauth.net/2/), and you'll also want to familiarize yourself with [PCO's Authentication docs](<https://developer.planning.center/docs/#/introduction/authentication>).

To get started, you'll need to register your OAuth app with PCO. To do this, sign  into your account at [api.planningcenteronline.com](https://api.planningcenteronline.com/). Click **Applications** in the toolbar and then click **Register one now** in under the My Developer Tokens (OAuth) heading. Fill out the required information and click **Submit**, and you'll see your generated client id and secret.

Now, you're ready to connect to the PCO API. The example below demonstrates authentication with OAuth. Note that you'll have significantly more work to do than with PAT; you'll need to use a browser to display PCO's authentication page with the appropriate parameters and have a redirect page which will be able to hand you the returned code parameter (which you'll use to get your access and refresh tokens). While most of the heavy lifting is up to you, pypco does provide a few convenience functions to help with the process as demonstrated in the example below.

```python
import pypco

# Generate the login URI
# note that valid scopes are: check_ins, giving, people, resources, and services
redirect_url = pypco.utils.get_browser_redirect_url("<CLIENT_ID_HERE>", "<REDIRECT_URI_HERE>", ["scope_1", "scope_2"])

# Now, you'll have the URI to which you need to send the user for authentication
# Here is where you would handle that and get back the code parameter PCO returns.

# For this example, we'll assume you've handled this and now have the code parameter
# stored in a variable named, appropriately, "code".

# Now, we'll get the OAuth access token json response using the code we received from PCO
token_dict = pypco.utils.get_oauth_access_token("<CLIENT_ID_HERE>", "<CLIENT_SECRET_HERE>", "<CODE_HERE>", "<REDIRECT_URI_HERE>")

# The response you'll receive from the get_oauth_access_token function will include your
# access token, your refresh token, and other metadata you may need later. You may wish/need to store this on disk as securely as possigle. Once you've gotten your access token, you can initialize a pypco object like this:
pco = pypco.PCO(token=token_dict['access_token'])

# Now, you're ready to go.
# Let's get a single person from your account and display their information
# We'll call the People endpoint's list() function, which returns an iterator
people = pco.people.people.list()
person = next(people)
print(person)
```

OAuth tokens will work for up to two hours after they have been issued, and can be renewed with a refresh token. Again, pypco helps you out here by providing a simple convenience function you can use to refresh OAuth tokens.

```python
import pypco

# Refresh the access token
token_dict = pypco.utils.refresh_access_token("<CLIENT_ID_HERE>", "<CLIENT_SECRET_HERE>", "<REFRESH_TOKEN_HERE>")

# You'll get back a response similar to what you got calling get_oauth_access_token
# the first time you authenticated your user against PCO. Now, you can initialize a PCO object and make some API calls.
pco = pypco.PCO(token=token_dict['access_token'])
people = pco.people.people.list()
person = next(people)
print(person)
```

## Conclusion

Once you've authenticated and been able to make a simple API call, you're good to go. Head over to the API Tour document for a brief tour of the pypco API; this document will show you how pypco calls relate to their PCO API counterparts. Once you've read through the API Tour, you should be ready to fully leverage the capabilities of pypco (and be done reading pypco documentation…you'll be able to know exactly what pypco calls to make by reading the PCO API docs).