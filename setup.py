# -*- coding: utf-8 -*-

import io
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = ''
with io.open('blox/_version.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

setup(
    name='blox',
    version=version,
    description='Fast binary data storage with blosc support.',
    author='Ivan Smirnov',
    author_email='i.s.smirnov@gmail.com',
    url='https://github.com/aldanor/blox',
    license='MIT',
    packages=['blox'],
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4'
        'Programming Language :: Python :: 3.5',
    ),
    install_requires=[
        'numpy', 'blosc', 'six'
    ],
    extras_require={
        'extras': ['ujson']
    }
)
