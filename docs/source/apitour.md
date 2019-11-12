# API Tour

## Introduction

Pypco aims to provide a Pythonic interface to the PCO REST API. To that end, rather than worrying about HTTP calls, pypco allows you to communicate with the PCO API using native Python code that does all of the transport-level work for you. The calls you'll make using pypco are easy to derive from the PCO API documentation once you understand pypco conventions. This API Tour will quickly introduce you to pypco conventions and get you on your way to working with your PCO data in Python.

For the purposes of this document, we'll assumed you've already been able to authenticate successfully using the methods described in the [Getting Started Guide](gettingstarted). Thus, each of the examples below will assume that you've already done something like the following to import the pypco module and initialize a PCO object:

```python
import pypco

pco = pypco.PCO("<APP_ID_HERE>", "<APP_SECRET_HERE>")
```

## Calling API Endpoints

Pypco uses a nested endpoint object hierarchy that corresponds exactly to the endpoint URLS from the PCO REST API. The easiest way to explain this is probably by example:

```python
# Endpoint to call (HTTP GET): https://api.planningcenteronline.com/people/v2/people
# (this gets a list of all the people in your PCO account)

# pypco call
people_iterator = pco.people.people.list()
```

To make this easy to follow, we'll break this call down into its component parts. The first part of the call is:

`pco.people`

We're assuming that we've already instantiated a PCO object from pypco and assigned it to the variable `pco`. Then, we're making a call to the People app. Hence, we have `pco.people`; this is selecting the People endpoint from our instance of the PCO class. Of course, we can substitute `people` here for any of the supported PCO apps, such as `services`, `giving`, etc. 

## CRUD: The Basics

### Reading Objects from PCO

We'll start with reading objects, as that's the simplest operation.



### Updating Objects in PCO

### Creating Objects in PCO

### Deleting Objects in PCO

