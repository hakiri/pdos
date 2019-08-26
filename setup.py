#!/usr/bin/env python3

from setuptools import setup

import sys
if sys.version_info < (3, 0):
    sys.stdout.write("Sorry, requires Python 3.x\n")
    sys.exit(1)

setup(
    name='pdos',
    version='0.1',
    platforms='Posix',
    python_requires=">=3.6",
    install_requires=[
        'grpcio>=1.22.0',
        'grpcio-tools>=1.22.0',
        'googleapis-common-protos>=1.6.0',
        'protobuf>=3.9.0',
        'gevent==1.4.0',
        'web3==4.9.2',
        'web3py>=0.1.20190709.1',
        'py-solc-x>=0.4.1',
    ],
    packages=[
        'proto',
        'pdos',
        'pdosd',
        'solidity',
        'utils',
    ],
    package_data={
        'proto': [
            'pdosd.proto',
        ],
        'pdosd': [
            'contracts/*',
        ],
        'solidity': [
            'contracts/*',
        ],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pdos=pdos.pdos:main',
            'pdosd=pdosd.pdosd:main'
        ],
    },
)
