# (c) 2013 Marcos Dione <mdione@grulic.org.ar>

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
import sys
import io
import os
import tempfile
import os.path

from ayrton.expansion import bash, default
import ayrton
from ayrton.execute import CommandNotFound

import logging
logger= logging.getLogger ('ayrton.tests.ayrton')

# create one of these
ayrton.runner= ayrton.Ayrton ()

class Argv (unittest.TestCase):

    def testEmpty (self):
        self.assertRaises (ValueError, ayrton.Argv, [])


    def testIter (self):
        data= ['foo', 'bar', 'baz']
        argv= ayrton.Argv (data)

        args= list (iter (argv))

        self.assertEqual (args, data[1:])


    def testLen (self):
        data= ['foo', 'bar', 'baz']
        argv= ayrton.Argv (data)

        l= len (argv)

        self.assertEqual (l, len (data)-1)


    def testPopFirst (self):
        data= ['foo', 'bar', 'baz']
        argv= ayrton.Argv (data)

        i= argv.pop (0)

        self.assertEqual (i, data[1])


class ScriptExecution (unittest.TestCase):
    """Runs tests from a script in disk, compares return value."""

    def setUp (self):
        self.runner= ayrton.Ayrton ()


    def doTest (self, file_name, expected=None, argv=None):
        if argv is not None:
            argv.insert (0, file_name)
        else:
            argv= [ file_name ]

        logger.debug (argv)
        result= self.runner.run_file (os.path.join ('ayrton/tests/scripts', file_name),
                                      argv=argv)
        if expected is not None:
            self.assertEqual (result, expected)


class MockedStdout (ScriptExecution):

    def setUp (self):
        super ().setUp ()

        # due to the interaction between file descriptors,
        # I better write this down before I forget

        # I save the old stdout in a new fd
        self.old_stdout= os.dup (1)
        logger.debug ('stdout saved in %s', self.old_stdout)

        # create a pipe; this gives me a read and write fd
        r, w= os.pipe ()
        logger.debug ('pipe for stdout: %d -> %d', w, r)

        # I replace the stdout with the write fd
        # this closes 1, but the original stdout is saved in old_stdout
        os.dup2 (w, 1)
        logger.debug ('redirecting stdout 1 -> %d', w)

        # now I have two fds pointing to the write end of the pipe, stdout and w
        # close w
        logger.debug ('closing %d', w)
        os.close (w)

        # create a file() from the reading fd
        # this DOES NOT create a new fd or file
        self.r= open (r, mode='rb')
        self.addCleanup (self.r.close)

        # the test will have to close stdin after performing what's testing
        # that's because otherwise the test locks at reading from the read end
        # because there's still that fd available for writing in the pipe
        # there is another copy of that fd, in the child side,
        # but that is closed when the process finished
        # there is still a tricky part to do on tearDownMockStdout()


    def tearDown (self):
        # restore sanity
        # original stdout into 1, even if we're leaking fd's
        logger.debug ('restoring stdout -> %d', self.old_stdout)
        os.dup2 (self.old_stdout, 1)
        logger.debug ('closing %d', self.old_stdout)
        os.close (self.old_stdout)
        logger.debug ('closing %d', self.r.fileno ())
        self.runner.wait_for_pending_children ()


    def doTest (self, script):
        super ().doTest (script)
        # close stdout as per the description of setUpMockStdout()
        os.close (1)


    def testStdout (self):
        self.doTest ('testStdout.ay')
        self.assertEqual (self.r.read (), b'foo\n')


    def testStdoutEqNone (self):
        self.doTest ('testStdoutEqNone.ay')
        # the output is empty, as it went to /dev/null
        self.assertEqual (self.r.read (), b'')


class CommandExecution (ScriptExecution):

    def testStdoutEqCapture (self):
        # echo adds the \n
        self.doTest ('testStdoutEqCapture.ay', 'foo\n')


    def testExitCodeOK (self):
        self.doTest ('testExitCodeOK.ay', 'yes!')


    def testExitCodeNOK (self):
        self.doTest ('testExitCodeNOK.ay', 'yes!')


    def testOptionErrexit (self):
        self.assertRaises (ayrton.CommandFailed, self.doTest, 'testOptionErrexit.ay')


    def testOptionMinus_e (self):
        self.assertRaises (ayrton.CommandFailed, self.doTest, 'testOptionMinus_e.ay')


    def testOptionPlus_e (self):
        self.doTest ('testOptionPlus_e.ay')


    def __testOptionETrue (self):
        self.assertRaises (ayrton.CommandFailed, self.doTest, 'testOptionETrue.ay')


    def testFails (self):
        self.doTest ('testFails.ay')


class NonWordExecutableNames (ScriptExecution):

    def setUp (self):
        super ().setUp ()

        self.old_path= os.environ['PATH']

        # add ayrton/tests/data to $PATH
        os.environ['PATH']+= os.pathsep+os.path.join (os.getcwd (),
                                                      'ayrton/tests/data')
        logger.debug (os.environ['PATH'])


    def tearDown (self):
        super ().tearDown ()

        os.environ['PATH']= self.old_path


    def testDotInExecutables (self):
        self.doTest ('testDotInExecutables.ay')


    def __testDashInExecutables (self):
        self.doTest ('testDashInExecutables.ay')


    def __testRelativeExecutables (self):
        self.doTest ('testRelativeExecutables.ay')


    def __testAbsoluteExecutables (self):
        self.doTest ('testAbsoluteExecutables.ay')


    def testNotExecuteLiteralMethods (self):
        self.doTest ('testNotExecuteLiteralMethods.ay')


class TempFile (ScriptExecution):

    def doTempFileTest (self, script, final_contents, initial_contents=None,
                        double_redirection=False):
        fh, file_name= tempfile.mkstemp ()
        logger.debug ('mkstemp() -> %d (%s)', fh, file_name)
        argv= [ file_name ]

        if double_redirection:
            fh2, file_name2= tempfile.mkstemp ()
            logger.debug ('mkstemp() -> %d (%s)', fh2, file_name2)
            logger.debug ('closing %d', fh2)
            os.close (fh2)
            argv.append (file_name2)

        if initial_contents is not None:
            logger.debug ('writing %r to %d (%s)', initial_contents, fh, file_name)
            os.write (fh, initial_contents)

        # I need to close it because I need it open after the test has run
        logger.debug ('closing %d', fh)
        os.close (fh)

        logger.debug (argv)
        self.doTest (script, argv=argv)

        if not double_redirection:
            f= open (file_name)
            logger.debug ('reading from %d (%s)', f.fileno (), file_name)
        else:
            f= open (file_name2)
            logger.debug ('reading from %d (%s)', f.fileno (), file_name2)
        contents= f.read ()
        logger.debug ('closing %d', f.fileno ())
        f.close ()

        self.assertEqual (contents, final_contents)

        os.unlink (file_name)
        if double_redirection:
            os.unlink (file_name2)


class RedirectionPiping (TempFile):

    def testLt (self):
        self.doTempFileTest ('testLt.ay', '42\n', initial_contents=b'42\n')


    def testGt (self):
        self.doTempFileTest ('testGt.ay', 'yes\n')


    def testGtToUnwritableFile (self):
        self.doTest ('testGtToUnwritableFile.ay')


    def testLtGt (self):
        # TODO: type mismatch
        self.doTempFileTest ('testLtGt.ay', '43\n', initial_contents=b'43\n',
                             double_redirection=True)


    def testRShift (self):
        self.doTempFileTest ('testRShift.ay', 'yes\nyes!\n')


    def testPipe (self):
        self.doTest ('testPipe.ay', 'setup.py\n')


    def testLongPipe (self):
        self.doTest ('testLongPipe.ay', '1\n')


class MiscTests (ScriptExecution):

    def testEnviron (self):
        self.doTest ('testEnviron.ay', '44\n')


    def testUnset (self):
        self.doTest ('testUnset.ay',  [ '45', 'yes' ])


    def testEnvVarAsGlobalVar (self):
        os.environ['testEnvVarAsGlobalVar'] = '46' # envvars are strings only
        self.doTest ('testEnvVarAsGlobalVar.ay', '46')


    def testExportSetsGlobalVar (self):
        self.doTest ('testExportSetsGlobalVar.ay', '47')


    def testCwdPwdRename (self):
        self.doTest ('testCwdPwdRename.ay', 'ayrton')


    def testWithCd (self):
        self.doTest ('testWithCd.ay',
                     os.path.split (os.getcwd ())[-1])


    def testShift (self):
        self.doTest ('testShift.ay', '48', argv=[ '48' ])


    def testShifts (self):
        self.doTest ('testShifts.ay', [ '49', '27' ], argv=[ '49', '27' ])


    def testShiftArray (self):
        self.doTest ('testShiftArray.ay', [ 1, 2 ])


    def testO (self):
        # this should not explode
        self.doTest ('testO.ay')


    def testComposing (self):
        # equivalent to testPipe()
        self.doTest ('testComposing.ay', 'setup.py\n')

    def testBg (self):
        '''This test takes some time...'''
        self.doTest ('testBg.ay', 'yes!')
        # the tests script does not wait for find to finish
        # so we do it here
        self.runner.wait_for_pending_children ()

    def testShortIter (self):
        '''This test takes some time...'''
        self.doTest ('testShortIter.ay', 'yes!')

    def testLongIter (self):
        '''This test takes some time...'''
        self.doTest ('testLongIter.ay', 'yes!')

    def testLongOutput (self):
        '''This test takes some time...'''
        self.doTest ('testLongOutput.ay', 'yes!')

    def testExit0 (self):
        self.doTest ('testExit0.ay', 0)

    def testExit1 (self):
        self.doTest ('testExit1.ay', 1)

    def testZUndefined(self):
        self.assertRaises(NameError, self.doTest, 'testZNotDefined.ay', True)

    def testZEmptyString(self):
        self.doTest('testZEmptyString.ay', True)

    def testZNone(self):
        self.doTest('testZNone.ay', True)

    def testZString(self):
        self.doTest('testZString.ay', False)

    def testZInt(self):
        self.doTest('testZInt.ay', False)

    def testZEnvVar(self):
        self.doTest('testZEnvVar.ay', False)

    def testDefine(self):
        self.doTest('testDefine.ay', None)

    def testDefine(self):
        self.doTest('testDefineValue.ay', 6)

    def testDefineAgain(self):
        self.doTest('testDefineAgain.ay', False)


class CommandDetection (ScriptExecution):

    def testSimpleCase (self):
        self.doTest ('testSimpleCase.ay')

    def testSimpleCaseFails (self):
        self.assertRaises (CommandNotFound, self.doTest,
                           'testSimpleCaseFails.ay')

    def testFromImport (self):
        self.doTest ('testFromImport.ay')

    def testFromImportFails (self):
        self.assertRaises (CommandNotFound, self.doTest,
                           'testFromImportFails.ay')

    def testFromImportAs (self):
        self.doTest ('testFromImportAs.ay')

    def testFromImportAsFails (self):
        self.assertRaises (CommandNotFound, self.doTest,
                           'testFromImportAsFails.ay')

    def testAssign (self):
        self.doTest ('testAssign.ay')

    def testDel (self):
        self.assertRaises (ayrton.CommandFailed, self.doTest, 'testDel.ay')

    def testDefFun1 (self):
        self.doTest ('testDefFun1.ay')

    def testDefFun2 (self):
        self.assertRaises (ayrton.CommandFailed, self.doTest, 'testDefFun2.ay')

    def testDefFunFails1 (self):
        self.doTest ('testDefFunFails1.ay')

    def testCallFun (self):
        self.doTest ('testCallFun.ay')

    def testCommandIsPresent (self):
        self.doTest ('testCommandIsPresent.ay')

    def testInstantiateClass (self):
        self.doTest ('testInstantiateClass.ay')

    def testUnknown (self):
        try:
            ayrton.main ('''foo''')
        except CommandNotFound:
            raise
        except NameError:
            pass
        self.assertRaises (NameError, ayrton.main, '''fff()''')
        self.assertRaises (CommandNotFound, ayrton.main, '''fff()''')

    def testForDefinesTarget (self):
        self.doTest ('testForDefinesTarget.ay')

    def testForDefinesTargets (self):
        self.doTest ('testForDefinesTargets.ay')

class Importing (ScriptExecution):

    def del_module (self, module_name):
        try:
            del sys.modules[module_name]
        except KeyError:
            # the module was not even created, ignore
            pass

    def testImport (self):
        self.doTest ('testImport.ay')

    def testImportLocalAy (self):
        self.addCleanup (self.del_module, 'testImportLocalAyModule')

        self.doTest ('testImportLocalAy.ay')

        self.assertEqual (self.runner.globals['testImportLocalAyModule'].foo, 42)

    def testImportLocalAyPackage (self):
        self.addCleanup (self.del_module, 'package')

        self.doTest ('testImportLocalAyPackage.ay')

        self.assertEqual (self.runner.globals['package'].bar, 24)
        package_relative_path= 'ayrton/tests/scripts/package'
        # so we ignore the leading abs path
        suffix_length= -len (package_relative_path)
        self.assertTrue (self.runner.globals['package'].__path__[0][suffix_length:],
                         package_relative_path)

    def testImportLocalAyPackageAyModule (self):
        self.addCleanup (self.del_module, 'package.ay_module')
        self.addCleanup (self.del_module, 'package')

        self.doTest ('testImportLocalAyPackageAyModule.ay')

        self.assertTrue (self.runner.globals['package'].ay_module.ay)

    def testImportLocalAyPackagePyModule (self):
        self.addCleanup (self.del_module, 'package.py_module')
        self.addCleanup (self.del_module, 'package')

        self.doTest ('testImportLocalAyPackagePyModule.ay')

        self.assertTrue (self.runner.globals['package'].py_module.py)

    def testImportLocalPy (self):
        self.doTest ('testImportLocalPy.ay')

    def testImportCallFromFunc (self):
        self.doTest ('testImportCallFromFunc.ay')

    def testImportFrom (self):
        self.doTest ('testImportFrom.ay')

    def testImportFromCallFromFunc (self):
        self.doTest ('testImportFromCallFromFunc.ay')

class ParsingErrors (unittest.TestCase):

    def testTupleAssign (self):
        ayrton.main ('''(a, b)= (1, 2)''')

    def testSimpleFor (self):
        ayrton.main ('''for a in (1, 2): pass''')

class ReturnValues (unittest.TestCase):

    def __testSimpleReturn (self):
        self.assertEqual (ayrton.main ('''return 50'''), 50)

    def testException (self):
        self.assertRaises (SystemError, ayrton.main, '''raise SystemError''')
