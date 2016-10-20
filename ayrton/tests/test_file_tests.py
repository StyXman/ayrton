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

    def test_f_symfile (self):
        name= self.touch_symlink ()
        self.assertTrue (-f (name))

    def test_f_dir (self):
        name= self.touch_dir ()
        self.assertFalse (-f (name))

    def test_f_symdir (self):
        name= self.touch_symlink (dir=True)
        self.assertFalse (-f (name))


    # TODO: -g


    def test_h_file (self):
        name= self.touch_file ()
        self.assertFalse (-h (name))

    def test_h_symfile (self):
        name= self.touch_symlink ()
        self.assertTrue (-h (name))

    def test_h_dir (self):
        name= self.touch_dir ()
        self.assertFalse (-h (name))

    def test_h_symdir (self):
        name= self.touch_symlink (dir=True)
        self.assertTrue (-h (name))


    # TODO: -k

    # TODO: -p


    def test_r_readable (self):
        name= self.touch_file ()
        self.assertTrue (-r (name))

    def test_r_unreadable (self):
        name= self.touch_file ()
        os.chmod (name, 0)
        self.assertFalse (-r (name))


    def test_s_empty (self):
        name= self.touch_file ()
        self.assertFalse (-s (name))

    def test_s_something (self):
        name= self.touch_file (text=b'foo')
        self.assertTrue (-s (name))


    # TODO: -u


    def test_w_writable (self):
        name= self.touch_file ()
        self.assertTrue (-w (name))

    def test_w_nonwritable (self):
        name= self.touch_file ()
        os.chmod (name, 0)
        self.assertFalse (-w (name))

    def test_x_file (self):
        name= self.touch_file ()
        # file are not executable by default
        self.assertFalse (-x (name))

    def test_x_dir (self):
        name= self.touch_dir ()
        # but dirs are
        self.assertTrue (-x (name))


    # TODO: -N

    # TODO: -S


    def test_nt_no_file2 (self):
        name1= self.touch_file ()
        name2= tempfile.mktemp (suffix='.ayrtmp')
        self.assertTrue (-nt (name1, name2))

    def test_nt_true (self):
        name2= self.touch_file ()
        # name1 must be newer than name2
        name1= self.touch_file ()
        self.assertTrue (-nt (name1, name2))

    def test_nt_false (self):
        # name1 must be older than name2
        name1= self.touch_file ()
        name2= self.touch_file ()
        self.assertTrue (-nt (name1, name2))


    def test_ot_no_file1 (self):
        name1= tempfile.mktemp (suffix='.ayrtmp')
        name2= self.touch_file ()
        self.assertTrue (-ot (name1, name2))

    def test_ot_true (self):
        # name1 must be older than name2
        name1= self.touch_file ()
        name2= self.touch_file ()
        self.assertTrue (-ot (name1, name2))

    def test_ot_false (self):
        name2= self.touch_file ()
        # name1 must be newer than name2
        name1= self.touch_file ()
        self.assertTrue (-ot (name1, name2))
