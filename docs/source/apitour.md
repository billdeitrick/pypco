# API Tour

## Introduction

This API Tour will quickly introduce you to pypco conventions and so you'll be on your way to building cool stuff. Once you've spent a few minutes learning the ropes with pypco, you'll spend the rest of your time directly in the PCO API docs to figure out how to craft your requests.

For the purposes of this document, we'll assume you've already been able to authenticate successfully using the methods described in the [Getting Started Guide](gettingstarted). Thus, each of the examples below will assume that you've already done something like the following to import the pypco module and initialize an instance of the PCO object:

```python
>>> import pypco

>>> pco = pypco.PCO("<APP_ID_HERE>", "<APP_SECRET_HERE>")
```

Also for purposes of this guide, we'll assume you're already somewhat familiar with the PCO API ([docs here](https://developer.planning.center/docs/#/introduction)). If you're not, you might want to read the [Introduction](https://developer.planning.center/docs/#/introduction) and then come back here.

### URL Passing and `api_base`

As you'll see shortly, for most requests you'll specify portions of the URL corresponding to the API endpoint against which you would like to make a REST call. You don't need to specify the protocol and hostname portions of the URL; these are automatically prepended for you whenever you pass a URL into pypco. Pypco refers to the automatically prepended protocol and hostname as `api_base`. By default, `api_base` is `https://api.planningcenteronline.com` (though an alternative can be [passed as an argument](pypco.html#module-pypco.pco)). So, you'll want to include a forward slash at the beginning of any URL argument you pass. Don't worry if this is confusing right now; it will all make sense once you've read the examples below.

Often times, you may find it would be easier to pass a URL to pypco that includes `api_base`. You might want to do this in situations where you've pulled a URL to a specific object in the PCO API directly from an attribute on an object you've already retrieved (such as a "links" attribute). Pypco has no problem if you include the `api_base` in a URL you pass in; it's smart enough to detect that it doesn't need to prepend `api_base` again in this situation so there's no need for you to worry about stripping it out.

## The Basics: GET, POST, PATCH, and DELETE

### GET: Retrieving Objects

Let's start with a simple GET request where we retrieve a specific person from the People API and print their name:

```python
# Retrieve the person with ID 71059458
# (GET https://api.planningcenteronline.com/people/v2/people/71059458)
>>> person = pco.get('/people/v2/people/71059458') # Returns a Dict
>>> print(person['data']['attributes']['name'])
John Smith
```

If you need to pass any URL parameters, you can pass them to `get()` as keyword arguments, like this:

```python
>>> person = pco.get('/people/v2/people/71059458', test='hello', test2='world')
```

This would result in the following request to the API: `GET https://api.planningcenteronline.com/people/v2/people/71059458?test=hello&test2=world`

Using keyword arguments you can pass any parameters supported by the PCO API for a given endpoint.

> **NOTE:** URL parameter keyword arguments must be passed as strings. If you are passing an object like a `dict` or a `list` for instance, cast it to a `str` and verify it is in the format required by the PCO API!

There may be times where you need to pass URL parameters that you can't pass as function arguments (for example, when the URL parameters contain characters that can't be used in a Python variable name). In these situations, create a `dict` and pass the keyword arguments using the double splat operator:

```python
>>> params = {
  'where[first_name]': 'pico',
  'where[last_name]': 'robot'
}
>>> result = pco.get('/people/v2/people', **params)
```

You can learn more about the `get()` function in the  [PCO module docs](pypco.html#pypco.pco.PCO.get).

### PATCH: Updating Objects

When altering existing objects in the PCO API, you only need to pass the attributes in your request payload that you wish to change. The easiest way to to generate the necessary payload for your request is using the [`template()` function](pypco.html#pypco.pco.PCO.template). The `template()` function takes the object type and attributes as arguments and returns a `dict` object that you can pass to `patch()` (which will serialize the object to JSON for you). There is, of course, no reason you have to use the `template()` function, but this is provided for you to help speed the process of generating request payloads.

In this example we'll change an existing person object's last name, using the `template()` function to generate the appropriate payload.

```python
# First we'll retrieve the existing person and print their last name
>>> person = pco.get('/people/v2/people/71059458') # Returns a Dict
>>> print(person['data']['attributes']['name'])
John Smith

# Next, we'll use the template() function to build our JSON payload
# for the PATCH request
>>> update_payload = pco.template('Person', {'last_name': 'Rolfe'})

# Perform the PATCH request; patch() will return the updated object
>>> updated_person = pco.patch(person['data']['links']['self'], payload=update_payload)
>>> print(updated_person['data']['attributes']['name'])
John Rolfe
```

Be sure to consult the PCO API Docs for whatever object you are attempting to update to ensure you are passing assignable attributes your payload. If you receive an exception when attempting to update an object, be sure to read [exception handling](#exception-handling) below to learn how to find the most information possible about what went wrong.

Aside from the `payload` keyword argument, any additional arguments you pass to the `patch()` function will be sent as query parameters with your request.

You can learn more about the `patch()` function in the [PCO module docs](pypco.html#pypco.pco.PCO.patch).

### POST: Creating Objects

Similarly to altering existing objects via a PATCH request, the first step towards creating new objects in the PCO API is generally using the [`template()` function](pypco.html#pypco.pco.PCO.template) to generate the necessary payload.

In the following example, we'll create a new person in PCO using the `template()` function to generate the payload for the request.

```python
# Create a payload for the request
>>> create_payload = pco.template(
  'Person',
  {
    'first_name': 'Benjamin',
    'last_name': 'Franklin',
    'nickname': 'Ben'
  }
)

# Create the person object and print the name attribute
>>> person = pco.post('/people/v2/people', payload=create_payload)
>>> print(person['data']['attributes']['name'])
Benjamin Franklin
```

Just like `patch()`, always be sure to consult the PCO API docs for the object type you are attempting to create to be sure you are passing assignable attributes in the correct format. If you do get stuck, the [exception handling](#exception-handling) section below will help you learn how to get the most possible information about what went wrong.

Also just like `patch()`, any keyword arguments you pass to `post()` aside from the `payload` argument will be added as parameters to your API request.

Aside from object creation, HTTP POST requests are also used by various PCO API endpoints for "Actions". These are endpoint-specific operations supported by various endpoints, such as the [Song Endpoint](https://developer.planning.center/docs/#/apps/services/2018-11-01/vertices/song). You can use the `post()` function for Action operations as needed; be sure to pass in the appropriate argument to the `payload` parameter  (as a `dict`, which will automatically be serialized to JSON for you).

You can learn more about the `post()` function in the [PCO module docs](pypco.html#pypco.pco.PCO.post).

### DELETE: Removing Objects

Removing objects is probably the simplest operation to perform. Simply pass the desired object's URL to the `delete()` function:

```python
>>> response = pco.delete('/people/v2/people/71661010')
>>> print(response)
<Response [204]>
```

Note that the `delete()` function returns a [Requests](https://requests.readthedocs.io/en/master/) `Response` object instead of a `dict` since the PCO API always returns an empty payload for a DELETE request. The `Response` object returned by a successful DELETE request will have a `status_code` value of 204.

As usual, any keyword arguments you pass to `delete()` will be passed to the PCO API as query parameters (though you typically won't need query parameters for DELETE requests).

You can learn more about the `delete()` function in the [PCO module docs](pypco.html#pypco.pco.PCO.delete).

## Advanced: Object Iteration and File Uploads

### Object Iteration with `iterate()`

Querying an API endpoint that returns a (possibly quite large) list of results is probably something you'll need to do at one time or another. To simplify this common use case, pypco provides the `iterate()` function. `iterate()` is a [generator function](https://wiki.python.org/moin/Generators) that performs GET requests against API endpoints that return lists of objects, transparently handling pagination.

Let's look at a simple example, where we iterate through all of the `person` objects in PCO People and print out their names:

```python
>>> for person in pco.iterate('/people/v2/people'):
>>>   print(person['data']['attributes']['name'])
John Rolfe
Benjamin Franklin
...
```

Just like `get()`, any keyword arguments you pass to `iterate()` will be added to your HTTP request as query parameters. For many API endpoints, this will allow you to build specific queries to pull data from PCO. In the example below, we demonstrate searching for all `person` objects with the last name "Rolfe". Note the use of the double splat operator to pass parameters as explained [above](#get-retrieving-objects).

```python
>>> params = {
  'where[last_name]': 'Rolfe'
}
>>> for person in pco.iterate('/people/v2/people', **params):
>>>		print(person['data']['attributes']['name'])
John Rolfe
...
```

Often you will want to use includes to return associated objects with your call to `iterate()`. To accomplish this, you can simply pass `includes` as a keyword argument to the `iterate()` function. To save you from having to find which includes are associated with a particular object yourself, `iterate()` will return objects to you with only their associated includes.

You can learn more about the `iterate()` function in the [PCO module docs](pypco.html#pypco.pco.PCO.iterate).

### File Uploads with `upload()`

Pypco provides a simple function to support file uploads to PCO (such as song attachments in Services, avatars in People, etc). To facilitate file uploads as described in the [PCO API docs for file uploads](https://developer.planning.center/docs/#/introduction/file-uploads), you'll first use the `upload()` function to upload files from your disk to PCO. This action will return to you a unique ID (UUID) for your newly uploaded file. Once you have the file UUID, you'll pass this to an endpoint that accepts a file.

In the example below, we upload a avatar image for a person in PCO People and associate it with the appropriate person object:

```python
# Upload the file, receive response containing UUID
>>> upload_response = pco.upload('john.jpg')
# Update the avatar attribute on the appropriate person object
# and print the resulting URL
>>> avatar_update = pco.template(
  		'Person', 
  		{'avatar': upload_response['data'][0]['id']}
		)
>>> person = pco.patch('/people/v2/people/71059458', payload=avatar_update)
>>> print(person['data']['attributes']['avatar'])
https://avatars.planningcenteronline.com/uploads/person/71059458-1578368234/avatar.2.jpg
```

As usual, any keyword arguments you pass to `upload()` will be passed to the PCO API as query parameters (though you typically won't need query parameters for file uploads).

You can learn more about the `upload()` function in the [PCO module docs](pypco.html#pypco.pco.PCO.upload).

## Exception Handling

Pypco provides custom exception types for error handling purposes. All exceptions are defined in the [exceptions](pypco.html#module-pypco.exceptions) module, and inherit from the base [PCOExceptions](pypco.html#pypco.exceptions.PCOException) class.

Most of the pypco exception classes are fairly mundane, though the [PCORequestException](pypco.html#pypco.exceptions.PCORequestException) class is worth a closer look. This exception is raised in circumstances where a connection was made to the API, but the API responds with a status code indicative of an error (other than a rate limit error, as these are handled transparently as discussed below). To provide as much helpful diagnostic information as possible, `PCORequestException` provides three attributes with more data about the failed request: `status_code`, `message`, and `response_body`. You can find more details about each of these attributes in the [PCORequestException Docs](pypco.html#pypco.exceptions.PCORequestException). A brief example is provided below showing what sort of information each of these variables might contain when a request raises this exception:

```python
# Create an invalid payload to use as an example
>>> bad_payload = pco.template(
			'Person',
  		{'bogus': 'bogus'}
	)

# Our bad payload will raise an exception...print out attributes
# from PCORequestException
>>> try:
>>>   result = pco.patch('/people/v2/people/71059458', payload=bad_payload)
>>>	except Exception as e:
>>>   print(f'{e.status_code}\n-\n{e.message}\n-\n{e.response_body}')
422
-
422 Client Error: Unprocessable Entity for url:
-
https://api.planningcenteronline.com/people/v2/people/71059458
{"errors":[{"status":"422","title":"Forbidden Attribute","detail":"bogus cannot be assigned"}]}  
```

You can find more information about all types of exceptions raised by pypco in the [PCOExceptions module docs](pypco.html#module-pypco.exceptions).

## Rate Limit Handling

Pypco automatically handles rate limiting for you. When you've hit your rate limit, pypco will look at the value of the `Retry-After` header from the PCO API and automatically pause your requests until your rate limit for the current period has expired. Pypco uses the `sleep()` function from Python's `time` package to do this. While the `sleep()` function isn't reliable as a measure of time per se because of the underlying kernel-level mechanisms on which it relies, it has proven accurate enough for this use case.