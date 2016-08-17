# -*- coding: utf-8 -*-

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

from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
import sys
import os
import os.path
import logging

logger= logging.getLogger ('ayrton.importer')

from ayrton.file_test import _a, _d
from ayrton import Ayrton
import ayrton.utils


class AyrtonLoader (Loader):

    @classmethod
    def exec_module (klass, module):
        # module is a freshly created, empty module
        # «the loader should execute the module’s code
        # in the module’s global name space (module.__dict__).»
        load_path= module.__spec__.origin
        logger.debug ('loading %s [%s]', module, load_path)
        # I *need* to polute the globals, so modules can use any of ayrton's builtins
        loader= Ayrton (g=module.__dict__)
        loader.run_file (load_path)

        # set the __path__
        # TODO: read PEP 420
        init_file_name= '__init__.ay'
        if load_path.endswith (init_file_name):
            # also remove the '/'
            module.__path__= [ load_path[:-len (init_file_name)-1] ]

        logger.debug3 ('module.__dict__: %s ', ayrton.utils.dump_dict (module.__dict__))

loader= AyrtonLoader ()


class AyrtonFinder (MetaPathFinder):

    @classmethod
    def find_spec (klass, full_name, paths=None, target=None):
        # full_name is the full python path (as in grandparent.parent.child)
        # and path is the path of the parent (in a list, see PEP 420);
        # if None, then we're loading a root module
        # let's start with a single file
        # TODO: read PEP 420 :)
        logger.debug ('searching for %s under %s for %s', full_name, paths, target)
        last_mile= full_name.split ('.')[-1]

        if paths is not None:
            python_path= paths  # search only there
        else:
            python_path= sys.path

        logger.debug (python_path)
        for path in python_path:
            full_path= os.path.join (path, last_mile)
            init_full_path= os.path.join (full_path, '__init__.ay')
            module_full_path= full_path+'.ay'

            logger.debug2 ('trying %s', init_full_path)
            if _d (full_path) and _a (init_full_path):
                logger.debug ('found package %s', full_path)
                return ModuleSpec (full_name, loader, origin=init_full_path)

            else:
                logger.debug2 ('trying %s', module_full_path)
                if _a (module_full_path):
                    logger.debug ('found module %s', module_full_path)
                    return ModuleSpec (full_name, loader, origin=module_full_path)

        logger.debug ('404 Not Found')
        return None

finder= AyrtonFinder ()


# I must insert it at the beginning so it goes before FileFinder
sys.meta_path.insert (0, finder)
