from __future__ import print_function

import setuptools

setuptools.setup(
    name="cfnresponse",
    version="1.0",
    author="Amazon Web Services",
    description="Setuptools packaging of cfnresponse.py -- Python module included in CloudFormation-based Python Lambda functions.",
    packages=setuptools.find_packages()
)