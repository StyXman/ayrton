# -*- coding: utf-8 -*-

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

from glob import glob
from functools import reduce

def glob_expand (s):
    # shamelessly insprired from sh.py
    # but we return a list with the string when there is no match
    # and we also handle lists of strings; we expand them independently
    if type (s)==str:
        l= [s]
    else:
        # otherwise we assume it's some kind of iterable
        l= s

    ans= []
    for s in l:
        a= glob (s)
        if a==[]:
            a= [s]

        # accumulate them
        ans+= a

    return ans

def brace_expand (s):
    seq= 0
    # we'll have a list and a dict
    # the list will hold all the values
    indexes= []
    # the dict will just hold those we're currently handling
    current= {}

    # iterate from left to right over the chars
    for i, c in enumerate (s):
        # if the char is {, try to find the first closing }
        # but if another { is found, use that as the matching one for the }
        if   c=='{' and s[i-1]!='\\':
            indexes.append ([seq, i])
            # we make sure we point to the same list,
             # so we can add the pointer to the closing bracket when we find it
            current[seq]= indexes[-1]
            seq+= 1
        elif c=='}' and s[i-1]!='\\':
            # we append to the element the pointer to the closing bracket
            try:
                current[seq-1].append (i)
                seq-= 1
            except KeyError:
                # there is no corresponding opening bracket; just ignore
                pass

    # print indexes
    # now we iterate over the found pairs and we expand from the outside to the inside
    for j, data in enumerate (indexes):
        if len (data)==3:
            # we have seq, left, right
            # print "iteration %d: %s, %s" % (j, s, data)
            seq, left_cb, right_cb= data

            prefix= s[:left_cb]
            postfix= s[right_cb+1:]
            body= s[left_cb+1:right_cb]

            # we cannot split just using split(',')
            # because that would see the possible commas of inner bracket pairs
            # we have to search for them, but skip the regions between brackets
            expanded= []
            last= 0
            split_here= False
            comma_found= False
            # index for the position in the original string of the beginning of
            # the current body starts
            # we need it because the indexes are base on the positions on the original string
            base= left_cb+1

            # print "%r %r %r" % (prefix, body, postfix)
            for i, c in enumerate (body):
                if c==',' and body[i-1]!='\\':
                    split_here= True
                    for seq, l, r in indexes[j+1:]:
                        if l>right_cb:
                            # stop searching, this pair is beyond us
                            break

                        orig_i= base+i
                        # print seq, l, orig_i, r

                        if l<orig_i and orig_i<r:
                            # print 'not splitting, comma @%d(%d) between {%d,%d}' % (orig_i, i, l, r)
                            split_here= False
                            # stop searching too
                            break

                    if split_here:
                        comma_found= True
                        expanded.append (body[last:i])
                        # print 'split!', expanded
                        last= i+1 # point to the next char, not the comma itself

            if comma_found:
                # add the last element
                expanded.append (body[last:])
                # print 'append', expanded

            if len (expanded)<2:
                return [ s ]

            # NOTE: this IS wrong; we should keep iterating, not recusrsing here
            return [ prefix+y+postfix for y in reduce (lambda x, y: x+y, [ brace_expand (x) for x in expanded ]) ]

    return glob_expand (s)

def backslash_descape (s):
    return s.replace ('\\', '')

def bash (s):
    return [ backslash_descape (x) for x in brace_expand (s) ]
