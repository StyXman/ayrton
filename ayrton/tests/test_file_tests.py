# (c) 2016 Marcos Dione <mdione@grulic.org.ar>

# This file is part of ayrton.
#
# ayrton is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ayrton is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ayrton.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import os
import tempfile

from ayrton.file_test import *
import ayrton
from ayrton.execute import CommandNotFound

import logging

logger= logging.getLogger ('ayrton.tests.file_tests')

# create one of these
# ayrton.runner= ayrton.Ayrton ()

class TestFalseBool (unittest.TestCase):

    def test_true (self):
        self.assertTrue (FalseBool (True))

    def test_false (self):
        self.assertFalse (FalseBool (False))

    def test_neg_true (self):
        self.assertTrue (-FalseBool (True))

    def test_neg_false (self):
        self.assertFalse (-FalseBool (False))

class FileTests (unittest.TestCase):

    def test_a_file (self):
        _, name= tempfile.mkstemp (suffix='.ayrtmp')
        self.addCleanup (os.unlink, name)

        self.assertTrue (-a (name))

    def test_a_dir (self):
        name= tempfile.mkdtemp (suffix='.ayrtmp')
        self.addCleanup (os.rmdir, name)

        self.assertTrue (-a (name))

    def test_a_symlink (self):
        name= tempfile.mkdtemp (suffix='.ayrtmp')
        self.addCleanup (os.unlink, name)
        name= tempfile.mktemp (suffix='.ayrton')

        self.assertTrue (-a (link))

    def test_d (self):
        name= tempfile.mkdtemp (suffix='.ayrtmp')
        self.addCleanup (os.rmdir, name)

        self.assertTrue (-d (name))

    def test_e (self):
        _, name= tempfile.mkstemp (suffix='.ayrtmp')
        self.addCleanup (os.unlink, name)

        self.assertTrue (-e (name))

    def test_f (self):
        _, name= tempfile.mkstemp (suffix='.ayrtmp')
        self.addCleanup (os.unlink, name)

        self.assertTrue (-f (name))
