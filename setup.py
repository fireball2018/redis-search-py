#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='redis_search',
    version='0.2',
    packages=['redis_search'],
    include_package_data = True,
    package_data = {
        '': ['data/*.dat'],
    },
    author='jiedan',
    author_email='lxb429@gmail.com',
    license='MIT License',
    description="High performance real-time search (Support Chinese), indexes store in Redis for Python",
    keywords ='redis search',
    url='https://github.com/jiedan/redis-search-py.git',
)