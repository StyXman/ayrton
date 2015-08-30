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
from itertools import chain
import os.path

def glob_expand (s):
    # shamelessly insprired from sh.py
    # but we return a list with the string when there is no match
    # and we also handle lists of strings; we expand them independently
    if type (s)==str:
        l= [ s ]
    else:
        # otherwise we assume it's some kind of iterable
        l= s

    ans= []
    for s in l:
        a= glob (s)
        if a==[]:
            a= [ s ]

        # accumulate them
        ans+= a

    return ans

class Group (object):
    def __init__ (self, left, right=None):
        self.left= left
        self.right= right

    def add_right (self, right):
        self.right= right

    def __repr__ (self):
        return "Group (%d, %r)" % (self.left, self.right)

    def __iter__ (self):
        yield self.left
        yield self.right

class ToExpand (object):
    def __init__ (self, s, indexes=None):
        self.text= s
        if indexes is None:
            self.find_indexes ()
        else:
            # I have to deep copy the Group
            self.indexes= []
            for i in indexes:
                self.indexes.append (Group (*list (i)))

    def find_indexes (self):
        self.indexes= []
        current= {}
        seq= 0

        # iterate from left to right over the chars
        for i, c in enumerate (self.text):
            # if the char is {, try to find the first closing }
            # but if another { is found, use that as the matching one for the }
            if   c=='{' and self.text[i-1]!='\\':
                data= Group (i)
                # print (data)
                self.indexes.append (data)
                # we make sure we point to the same list,
                # so we can add the pointer to the closing bracket when we find it
                current[seq]= data
                seq+= 1
            elif c=='}' and self.text[i-1]!='\\':
                # we append to the element the pointer to the closing bracket
                try:
                    data= current[seq-1]
                    data.add_right (i)
                    # print (data)
                    seq-= 1
                except KeyError:
                    # there is no corresponding opening bracket; just ignore
                    pass

        # remove indexes for unmatched open brackes
        # unmatched closing brackets are ignored in the try/except up there
        self.indexes= [ i for i in self.indexes if i.right is not None ]
        # print (self.indexes)

    def expand_one (self):
        "expand the more-to-the-left/outer bracket, return a list of ToExpand's"
        data= self.indexes.pop (0)

        left_cb, right_cb= data
        prefix= self.text[:left_cb]
        # includes the {}'s
        body= self.text[left_cb:right_cb+1]
        postfix= self.text[right_cb+1:]
        # print ("pre:%r b:%r post:%r" % (prefix, body, postfix))

        # will hold the expansion of the body
        expanded= []
        # do not count the opening bracket
        last= 1
        split_here= False
        comma_found= False
        # index for the position in the original string of the beginning of
        # the current body starts
        # we need it because the indexes are base on the positions on the original string
        base= left_cb+1

        for i, c in enumerate (body):
            if c==',' and body[i-1]!='\\':
                split_here= True
                # check if this comma belongs to a inner group
                for l, r in self.indexes:
                    # TODO: show that this cannot actually happen
                    if l>right_cb:
                        # stop searching, this pair is beyond us
                        break

                    orig_i= base+i
                    # print (s, l, orig_i, r)

                    if l<orig_i and orig_i<r:
                        # print 'not splitting, comma @%d(%d) between {%d,%d}' % (orig_i, i, l, r)
                        split_here= False
                        # stop searching too
                        break

                if split_here:
                    comma_found= True
                    dst= body[last:i]
                    te= ToExpand (prefix+dst+postfix)
                    expanded.append (te)
                    # print ('split!', expanded)
                    last= i+1 # point to the next char, not the comma itself

        # only add the last element if a comma was found
        if comma_found:
            # do not count the closing bracket
            dst= body[last:-1]
            te= ToExpand (prefix+dst+postfix)
            expanded.append (te)
            # print ('append', expanded)
        else:
            # otherwise, just leave untouched
            # (except for the index we already removed at the beginning of this method)
            expanded.append (self)

        return expanded

    def fully_expanded (self):
        # just check how many indexes are left
        return len (self.indexes)==0

    def __repr__ (self):
        return "ToExpand (%s, %s)" % (self.text, self.indexes)

def brace_expand (s):
    # NOTE: this function is O(N) in several ways
    if type (s)==str:
        l= [ s ]
    else:
        # otherwise we assume it's some kind of iterable
        l= s

    ans= []

    for s in l:
        todo= [ ToExpand (s) ]

        while (len (todo)>0):
            # print (todo)
            te= todo.pop (0)

            if not te.fully_expanded ():
                new_ones= te.expand_one ()
                for index, new in enumerate (new_ones):
                    if new.fully_expanded ():
                        ans.append (new.text)
                    else:
                        todo.insert (index, new)
            else:
                ans.append (te.text)

    return ans

def backslash_descape (s):
    if type (s)==str:
        ans= s.replace ('\\', '')
    else:
        # otherwise we assume it's some kind of iterable
        ans= [ s1.replace ('\\', '') for s1 in s ]

    return ans

def tilde_expand (s):
    if type (s)==str:
        ans= os.path.expanduser (s)
    else:
        # otherwise we assume it's some kind of iterable
        ans= [ os.path.expanduser (s1) for s1 in s ]

    return ans

def bash (s, single=False):
    data= backslash_descape (glob_expand (tilde_expand (brace_expand (s))))
    if single and len(data)==1:
        data= data[0]
    return data
