#!/usr/bin/env python
import os
import sys

from setuptools import setup, find_packages

requires = [
    "click==6.6",
    "PyYAML==3.12"
]

setup_options = dict(
    name='preprocess-swagger-input',
    version='0.1',
    description='preprocess-swagger-input CLI',
    author='Benn Linger',
    packages=find_packages(exclude=['tests*']),
    install_requires=requires,
    include_package_data=True,
    entry_points = '''
        [console_scripts]
        preprocess-swagger-input=preprocess_swagger_input.cli:cli
    '''
)

setup(**setup_options)