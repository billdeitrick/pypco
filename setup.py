
from setuptools import (
    setup,
    find_packages
)

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='pypco',
    version='1.1.0',
    description='A Python wrapper for the Planning Center Online API.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/billdeitrick/pypco',
    author='Bill Deitrick',
    author_email='hello@billdeitrick.com',
    python_requires='>=3.6.0',
    license='MIT',
    packages=find_packages(
        exclude=[
            'tests.*',
            'tests'
        ]
    ),
    install_requires=[
        'requests'
    ],
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries'
    ]
)
