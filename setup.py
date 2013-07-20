#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2013 Marcos Dione <mdione@grulic.org.ar>
# for licensing details see the file LICENSE.txt

from distutils.core import setup
import ayrton

setup (
    name='ayrton',
    version= ayrton.__version__,
    description= 'a shell-like scripting language on top of Python and python-sh.',
    author= 'Marcos Dione',
    author_email= 'mdione@grulic.org.ar',
    url= 'https://github.com/StyXman/ayrton',
    packages= [ 'ayrton' ],
    scripts= [ 'bin/ayrton' ],
    )
