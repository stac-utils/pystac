#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
from glob import glob
import io
from os.path import (
    join,
    dirname,
    basename,
    splitext
)

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

requirements = [
    read('requirements.txt')
]

setup_requirements = [
    # TODO(notthatbreezy): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pystac',
    version='0.1.0',
    description="Python command line utilities for interacting with and creating STAC compliant files.",
    long_description=readme + '\n\n' + history,
    author="Raster Foundry",
    author_email='info@rasterfoundry.com',
    url='https://github.com/notthatbreezy/pystac',
    packages=find_packages(),
    py_modules=[splitext(basename(path))[0] for path in glob('pystac/*.py')],
    entry_points={
        'console_scripts': [
            'pystac=pystac.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='pystac',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
