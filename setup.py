#!/usr/bin/env python

from distutils.core import setup

setup(name='asynczip',
      version='1.0',
      description='Asynchronous `zip` like aggregator for `async for`',
      long_description=open('README.md', 'rt').read(),
      author='Julien Palard',
      author_email='julien@palard.fr',
      url='https://github.com/JulienPalard/asynczip',
      py_modules='asynczip',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License']
     )
