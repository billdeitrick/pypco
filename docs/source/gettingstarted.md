# Getting Started

## Introduction

Pypco is an object-oriented, Pythonic client providing a Python interface to the [Planning Center Online](https://planning.center) API. This means you can stop worrying about individual HTTP requests, formatting JSON, dealing with rate limiting, etc. Pypco takes handles all of this for you, and lets you quickly start working with your PCO data.

Below you'll find some brief information about pypco's design goals and features. If you're not interested, feel free to jump right to [installation](#installation).

### Design Goals

* **Ease of use.** Pypco is designed first and foremost to be easy and intuitive to use. If there's a choice between implementing some functionality in pypco the "easy way" and making pypco easier to use, always err on the side of making pypco easier to use.
* **Helpful abstraction.** Pypco aims to abstract away all of the boilerplate stuff you need to do when connecting to the PCO API. Spend your time getting stuff done instead of writing HTTP requests.
* **REST API Parity.** You shouldn't have to spend lots of time reading the pypco documentation to figure out how to do something. Once you learn the simple idioms pypco uses, you should spend most of your time directly in the PCO API docs and know exactly what pypco calls to make to get what you want.
* **Full REST API support.** Pypco aims to support all functionality available in the PCO REST API. This doesn't mean every possible call is supported--sometimes there are multiple ways of doing the same thing, or certain calls that aren't needed to accomplish some task. The goal is to provide at least one supported way to accomplish any task supported by the REST API.

### Features

* **Native Python.** Interact with the PCO API using Pythonic code. Pypco will build HTTP requests for you and let you manipulate objects from PCO as native Python objects.
* **Automatic rate limiting management.** Pypco automatically handles rate limiting. When your calls are rate limited, pypco will automatically slow down for you. This means that your application doesn't have to be concerned about rate limiting at all--you can forget it exists.
* **Full CRUD support.** Create, read, update, and delete objects as supported by the PCO API. 

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