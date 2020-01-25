# Getting Started

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

PAT authentication is the simplest method (and probably what you'll use if you're wanting to kick the tires), so we'll start there.

First, you'll need to generate your application id and secret. Sign into your account at [api.planningcenteronline.com](https://api.planningcenteronline.com/). Click **Applications** in the toolbar and then click **New Personal Access Token** under the Personal Access Tokens heading. Enter a description of your choosing, and select the desired API version for your app. Pypco can support any API version or combination of versions. Click **Submit**, and you'll see your generated token. 

Now, you're ready to connect to the PCO API. The example below demonstrates authentication with a PAT and executes a simple query to get and display single person from your account.

```python
import pypco

# Get an instance of the PCO object using your personal access token.
pco = pypco.PCO("<APPLICATION_ID_HERE>", "<APPLICATION_SECRET_HERE>")

# Get a single person from your account and display their information
# The iterate() function provides an easy way to retrieve lists of objects
# from an API endpoint, and automatically handles pagination
people = pco.iterate('/people/v2/people')
person = next(people)
print(person)
```

If you can run the above example and see output for one of the people in your PCO account, you have successfully connected to the API. Continue to the [API Tour](apitour) to learn more, or learn about OAuth Authentication below.

### OAuth Authentication

OAuth is the more complex method for authenticating against PCO, but is what you'll want to use if you're building an app that accesses third-party data. 

Before diving in, it's helpful to have an understanding of OAuth basics, both in general and as they apply to the PCO API specifically. You'll want to familiarize yourself with [PCO's Authentication docs](https://developer.planning.center/docs/#/introduction/authentication), and if you're looking to learn more about OAuth in particular you can learn everything you need to know over at [oauth.net](https://oauth.net/2/).

To get started, you'll need to register your OAuth app with PCO. To do this, sign  into your account at [api.planningcenteronline.com](https://api.planningcenteronline.com/). Click **Applications** in the toolbar and then click **New Application** under the My Developer Tokens (OAuth) heading. Fill out the required information and click **Submit**, and you'll see your generated client id and secret.

Now, you're ready to connect to the PCO API. The example below demonstrates authentication with OAuth. Note that you'll have significantly more work to do than with PAT; you'll need to use a browser to display PCO's authentication page with the appropriate parameters and have a redirect page which will be able to hand you the returned code parameter (which you'll use to get your access and refresh tokens). While most of the heavy lifting is up to you, pypco does provide a few convenience functions to help with the process as demonstrated in the example below.

```python
import pypco

# Generate the login URI
redirect_url = pypco.get_browser_redirect_url(
    "<CLIENT_ID_HERE>",
    "<REDIRECT_URI_HERE>",
    ["scope_1", "scope_2"]
)

# Now, you'll have the URI to which you need to send the user for authentication
# Here is where you would handle that and get back the code parameter PCO returns.

# For this example, we'll assume you've handled this and now have the code
# parameter returned from the API

# Now, we'll get the OAuth access token json response using the code we received from PCO
token_response = pypco.get_oauth_access_token(
    "<CLIENT_ID_HERE>",
    "<CLIENT_SECRET_HERE>",
    "<CODE_HERE>",
    "<REDIRECT_URI_HERE>"
)

# The response you'll receive from the get_oauth_access_token function will include your
# access token, your refresh token, and other metadata you may need later.
# You may wish/need to store this entire response on disk as securely as possible.
# Once you've gotten your access token, you can initialize a pypco object like this:
pco = pypco.PCO(token=token_response['access_token'])

# Now, you're ready to go.
# The iterate() function provides an easy way to retrieve lists of objects
# from an API endpoint, and automatically handles pagination
people = pco.iterate('/people/v2/people')
person = next(people)
print(person)
```

OAuth tokens will work for up to two hours after they have been issued, and can be renewed with a refresh token. Again, pypco helps you out here by providing a simple convenience function you can use to refresh OAuth tokens.

```python
import pypco

# Refresh the access token
token_response = pypco.get_oauth_refresh_token("<CLIENT_ID_HERE>", "<CLIENT_SECRET_HERE>", "<REFRESH_TOKEN_HERE>")

# You'll get back a response similar to what you got calling get_oauth_access_token
# the first time you authenticated your user against PCO. Now, you can initialize a PCO object and make some API calls.
pco = pypco.PCO(token=token_response['access_token'])
people = pco.iterate('/people/v2/people')
person = next(people)
print(person)
```

## Conclusion

Once you've authenticated and been able to make a simple API call, you're good to go. Head over to the [API Tour](apitour) document for a brief tour of the pypco API; this document will show you how pypco calls relate to their PCO API counterparts. Once you've read through the API Tour, you should be ready to fully leverage the capabilities of pypco (and hopefully be done reading pypco documentation…you'll be able to know exactly what pypco calls to make by reading the PCO API docs).