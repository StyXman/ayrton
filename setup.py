#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2013 Marcos Dione <mdione@grulic.org.ar>
# for licensing details see the file LICENSE.txt

from distutils.core import setup
from distutils.extension import Extension
import ayrton

setup (
    name='ayrton',
    version= ayrton.__version__,
    description= 'a shell-like scripting language on top of Python and python-sh.',
    author= 'Marcos Dione',
    author_email= 'mdione@grulic.org.ar',
    url= 'https://github.com/StyXman/ayrton',
    packages= [ 'ayrton' ],
    ext_modules= [ Extension ('ayrton._ast', [ 'ayrton/ast.c' ]) ],
    scripts= [ 'bin/ayrton' ],
    license= 'GPLv3',
    classifiers= [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Topic :: System',
        'Topic :: System :: Systems Administration',
        ],
    )
