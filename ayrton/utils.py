# -*- coding: utf-8 -*-

# (c) 2015 Marcos Dione <mdione@grulic.org.ar>

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

import logging
import functools
from selectors import DefaultSelector, EVENT_READ
import os
from socket import socket
import itertools
import errno
import paramiko.channel
import traceback

import logging
logger= logging.getLogger ('ayrton.utils')


# TODO: there's probably a better way to do this
def debug2 (self, msg, *args, **kwargs):  # pragma: no cover
    if self.manager.disable>=logging.DEBUG2:
        return

    if logging.DEBUG2>=self.getEffectiveLevel ():
        self._log (logging.DEBUG2, msg, args, **kwargs)


def debug3 (self, msg, *args, **kwargs):  # pragma: no cover
    if self.manager.disable>=logging.DEBUG3:
        return

    if logging.DEBUG3>=self.getEffectiveLevel ():
        self._log (logging.DEBUG3, msg, args, **kwargs)


def patch_logging ():
    # based on https://mail.python.org/pipermail/tutor/2007-August/056243.html
    logging.DEBUG2= 9
    logging.DEBUG3= 8

    logging.addLevelName (logging.DEBUG2, 'DEBUG2')
    logging.addLevelName (logging.DEBUG3, 'DEBUG3')

    logging.Logger.debug2= debug2
    logging.Logger.debug3= debug3


patch_logging ()


def any_comparator (a, b):  # pragma: no cover
    try:
        if a==b:
            return 0
        elif a<b:
            return -1
        else:
            return 1
    except TypeError:
        return any_comparator (str (type (a)), str (type (b)))


def dump_dict (d, level=1):  # pragma: no cover
    if d is not None:
        strings= []

        if level==0:
            strings.append ("{\n")
        for k in sorted (d.keys (), key=functools.cmp_to_key (any_comparator)):
            v= d[k]
            if type (v)!=dict:
                strings.append ("%s%r: %r,\n" % ( '    '*level, k, v ))
            else:
                strings.append ("%s%r: {\n"   % ( '    '*level, k))
                strings.extend (dump_dict (v, level+1))
                strings.append ("%s},\n"      % ( '    '*level, ))
        if level==0:
            strings.cappend ("}\n")

        return ''.join (strings)
    else:
        return 'None'


def read (src, buf_len):
    if isinstance (src, int):
        return os.read (src, buf_len)
    elif isinstance (src, socket):
        return src.recv (buf_len)
    elif isinstance (src, paramiko.channel.Channel):
        return os.read (src.fileno (), buf_len)
    else:
        return src.read (buf_len)


def write (dst, data):
    if isinstance (dst, int):
        return os.write (dst, data)
    elif isinstance (dst, socket):
        return dst.send (data)
    else:
        ans= dst.write (data)
        dst.flush ()

        return ans


def close (f):
    logger.debug ('closing %s', f)
    try:
        if isinstance (f, int):
            os.close (f)
        else:
            f.close ()
    except OSError as e:
        logger.debug ('closing gave %s', e)
        if e.errno!=errno.EBADF:
            raise


def copy_loop (copy_to, finished=None, buf_len=10240):
    """copy_to is a dict(in: out). When any in is ready to read, data is read
    from it and writen in its out. When any in is closed, it's removed from
    copy_to. finished is a pipe; when data comes from the read end, or when
    no more ins are present, the loop finishes."""
    if finished is not None:
        copy_to[finished]= None

    # NOTE:
    # os.sendfile (self.dst, self.src, None, 0)
    # OSError: [Errno 22] Invalid argument
    # and splice() is not available
    # so, copy by hand
    selector = DefaultSelector ()
    for src in copy_to.keys ():
        if (     not isinstance (src, int)
                and (   getattr (src, 'fileno', None) is None
                    or not isinstance (src.fileno(), int)) ):
            logger.debug ('type mismatch: %s', src)
        else:
            logger.debug ("registering %s for read", src)
            # if finished is also one of the srcs, then register() complains
            try:
                selector.register (src, EVENT_READ)
            except KeyError:
                pass

    def close_file (f):
        if f in copy_to:
            del copy_to[f]

        try:
            selector.unregister (i)
        except KeyError:
            pass

        close (f)

    while len (copy_to)>0:
        logger.debug (copy_to)

        events= selector.select ()
        for key, _ in events:
            logger.debug ("%s is ready to read", key)
            i= key.fileobj

            # for error in e:
            #     logger.debug ('%s error')
                # TODO: what?

            o= copy_to[i]

            try:
                data= read (i, buf_len)
                logger.debug2 ('%s -> %s: %s', i, o, data)

            # ValueError: read of closed file
            except (OSError, ValueError) as e:
                logger.debug ('stopping copying for %s', i)
                logger.debug (traceback.format_exc ())
                close_file (i)
                break
            else:
                if len (data)==0:
                    logger.debug ('stopping copying for %s, no more data', i)
                    close_file (i)

                    if finished is not None and i==finished:
                        logger.debug ('finishing')
                        # quite a hack :)
                        copy_to= {}

                        break
                else:
                    write (o, data)

    selector.close ()
    logger.debug ('over and out')
