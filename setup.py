#!/usr/bin/env python

from os.path import exists
from setuptools import setup, find_packages

setup(
    name='factorio-status-ui',
    version=open('VERSION').read().strip(),
    author='Adam Charnock',
    author_email='adam@adamcharnock.com',
    packages=find_packages(),
    scripts=[],
    url='https://github.com/adamcharnock/factorio-status-ui',
    license='MIT',
    description='Simple web UI for Factorio headless servers',
    long_description=open('README.rst').read() if exists("README.rst") else "",
    install_requires=[
        'python-valve==0.2.1',
        'aiohttp==3.6.2',
        'aiohttp_jinja2==1.2.0',
    ],
    # Ensure we include files from the manifest
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'factorio_status_ui = factorio_status_ui.serve:main'
        ]
    }
)
