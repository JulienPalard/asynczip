#!/usr/bin/env python

from distutils.core import setup

setup(name='asynczip',
      version='1.0',
      description='Asynchronous `zip` like aggregator for `async for`',
      long_description=open('README.md', 'rt').read(),
      author='Julien Palard',
      author_email='julien@palard.fr',
      keywords=['asyncio', 'zip', 'select', 'async for', 'async'],
      url='https://github.com/JulienPalard/asynczip',
      download_url='https://github.com/julienpalard/AsyncZip/tarball/1.0',
      py_modules='asynczip',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License']
     )
