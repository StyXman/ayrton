#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2013 Marcos Dione <mdione@grulic.org.ar>
# for licensing details see the file LICENSE.txt

from distutils.core import setup
import ayrton

setup (
    name='ayrton',
    version= ayrton.__version__,
    description= 'a shell-like scripting language based on Python3.',
    author= 'Marcos Dione',
    author_email= 'mdione@grulic.org.ar',
    url= 'https://github.com/StyXman/ayrton',
    packages= [ 'ayrton', 'ayrton.parser', 'ayrton.parser.pyparser',
               'ayrton.parser.astcompiler' ],
    package_data= {
        'ayrton.parser.pyparser': [ 'data/Grammar3.3' ],
        },
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
