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

    def touch_file (self, text=None):
        fd, name= tempfile.mkstemp (suffix='.ayrtmp')
        # self.addCleanup (os.unlink, name)

        if text is not None:
            os.write (fd, text)

        os.close (fd)

        return name


    def touch_dir (self):
        name= tempfile.mkdtemp (suffix='.ayrtmp')
        self.addCleanup (os.rmdir, name)

        return name


    def touch_symlink (self, dir=False):
        if dir:
            name= self.touch_dir ()
        else:
            name= self.touch_file ()

        # yes, mktemp() is deprecated, but this is a bloody test
        # and there's no mkltemp()
        link= tempfile.mktemp (suffix='.ayrtmp')
        os.symlink (name, link)
        self.addCleanup (os.unlink, link)

        return link


    def test_a_file (self):
        name= self.touch_file ()
        self.assertTrue (-a (name))

    def test_a_symlink (self):
        name= self.touch_symlink ()
        self.assertTrue (-a (name))

    def test_a_dir (self):
        name= self.touch_dir ()
        self.assertTrue (-a (name))

    # TODO: -b

    # TODO: -c


    def test_d_file (self):
        name= self.touch_file ()
        self.assertFalse (-d (name))

    def test_d_symfile (self):
        name= self.touch_symlink ()
        self.assertFalse (-d (name))

    def test_d_dir (self):
        name= self.touch_dir ()
        self.assertTrue (-d (name))

    def test_d_symdir (self):
        name= self.touch_symlink (dir=True)
        self.assertTrue (-d (name))


    def test_e (self):
        name= self.touch_file ()
        self.assertTrue (-e (name))


    def test_f_file (self):
        name= self.touch_file ()
        self.assertTrue (-f (name))
