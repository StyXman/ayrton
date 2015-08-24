#! /usr/bin/env python
"""Module gendfa

Generates finite state automata for recognizing Python tokens.  These are hand
coded versions of the regular expressions originally appearing in Ping's
tokenize module in the Python standard library.

When run from the command line, this should pretty print the DFA machinery.

To regenerate the dfa, run::

    $ python gendfa.py > dfa_generated.py

$Id: genPytokenize.py,v 1.1 2003/10/02 17:37:17 jriehl Exp $
"""

from pypy.interpreter.pyparser.pylexer import *
from pypy.interpreter.pyparser.automata import NonGreedyDFA, DFA, DEFAULT

NON_ASCII = "\x80"

def makePyPseudoDFA ():
    import string
    states = []
    def makeEOL():
        return group(states,
                     newArcPair(states, "\n"),
                     chain(states,
                           newArcPair(states, "\r"),
                           maybe(states, newArcPair(states, "\n"))))
    # ____________________________________________________________
    def makeLineCont ():
        return chain(states,
                     newArcPair(states, "\\"),
                     makeEOL())
    # ____________________________________________________________
    # Ignore stuff
    def makeWhitespace ():
        return any(states, groupStr(states, " \f\t"))
    # ____________________________________________________________
    def makeComment ():
        return chain(states,
                     newArcPair(states, "#"),
                     any(states, notGroupStr(states, "\r\n")))
    # ____________________________________________________________
    #ignore = chain(states,
    #               makeWhitespace(),
    #               any(states, chain(states,
    #                                 makeLineCont(),
    #                                 makeWhitespace())),
    #               maybe(states, makeComment()))
    # ____________________________________________________________
    # Names
    name = chain(states,
                 groupStr(states, string.letters + "_" + NON_ASCII),
                 any(states, groupStr(states,
                                      string.letters + string.digits + "_" +
                                      NON_ASCII)))
    # ____________________________________________________________
    # Digits
    def makeDigits ():
        return groupStr(states, "0123456789")
    # ____________________________________________________________
    # Integer numbers
    hexNumber = chain(states,
                      newArcPair(states, "0"),
                      groupStr(states, "xX"),
                      atleastonce(states,
                                  groupStr(states, "0123456789abcdefABCDEF")))
    octNumber = chain(states,
                      newArcPair(states, "0"),
                      groupStr(states, "oO"),
                      groupStr(states, "01234567"),
                      any(states, groupStr(states, "01234567")))
    binNumber = chain(states,
                      newArcPair(states, "0"),
                      groupStr(states, "bB"),
                      atleastonce(states, groupStr(states, "01")))
    decNumber = chain(states,
                      groupStr(states, "123456789"),
                      any(states, makeDigits()))
    zero = chain(states,
                 newArcPair(states, "0"),
                 any(states, newArcPair(states, "0")))
    intNumber = group(states, hexNumber, octNumber, binNumber, decNumber, zero)
    # ____________________________________________________________
    # Exponents
    def makeExp ():
        return chain(states,
                     groupStr(states, "eE"),
                     maybe(states, groupStr(states, "+-")),
                     atleastonce(states, makeDigits()))
    # ____________________________________________________________
    # Floating point numbers
    def makeFloat ():
        pointFloat = chain(states,
                           group(states,
                                 chain(states,
                                       atleastonce(states, makeDigits()),
                                       newArcPair(states, "."),
                                       any(states, makeDigits())),
                                 chain(states,
                                       newArcPair(states, "."),
                                       atleastonce(states, makeDigits()))),
                           maybe(states, makeExp()))
        expFloat = chain(states,
                         atleastonce(states, makeDigits()),
                         makeExp())
        return group(states, pointFloat, expFloat)
    # ____________________________________________________________
    # Imaginary numbers
    imagNumber = group(states,
                       chain(states,
                             atleastonce(states, makeDigits()),
                             groupStr(states, "jJ")),
                       chain(states,
                             makeFloat(),
                             groupStr(states, "jJ")))
    # ____________________________________________________________
    # Any old number.
    number = group(states, imagNumber, makeFloat(), intNumber)
    # ____________________________________________________________
    # Funny
    operator = group(states,
                     chain(states,
                           chainStr(states, "**"),
                           maybe(states, newArcPair(states, "="))),
                     chain(states,
                           chainStr(states, ">>"),
                           maybe(states, newArcPair(states, "="))),
                     chain(states,
                           chainStr(states, "<<"),
                           maybe(states, newArcPair(states, "="))),
                     chainStr(states, "<>"),
                     chainStr(states, "!="),
                     chainStr(states, "->"),
                     chain(states,
                           chainStr(states, "//"),
                           maybe(states, newArcPair(states, "="))),
                     chain(states,
                           groupStr(states, "+-*/%&|^=<>"),
                           maybe(states, newArcPair(states, "="))),
                     newArcPair(states, "~"))
    bracket = groupStr(states, "[](){}")
    special = group(states,
                    makeEOL(),
                    chainStr(states, "..."),
                    groupStr(states, "@:;.,`"))
    funny = group(states, operator, bracket, special)
    # ____________________________________________________________
    def makeStrPrefix ():
        return group(states,
                     chain(states,
                           maybe(states, groupStr(states, "rR")),
                           maybe(states, groupStr(states, "bB"))),
                     chain(states,
                           maybe(states, groupStr(states, "bB")),
                           maybe(states, groupStr(states, "rR"))),
                     maybe(states, groupStr(states, "uU")))
    # ____________________________________________________________
    contStr = group(states,
                    chain(states,
                          makeStrPrefix(),
                          newArcPair(states, "'"),
                          any(states,
                              notGroupStr(states, "\r\n'\\")),
                          any(states,
                              chain(states,
                                    newArcPair(states, "\\"),
                                    newArcPair(states, DEFAULT),
                                    any(states,
                                        notGroupStr(states, "\r\n'\\")))),
                          group(states,
                                newArcPair(states, "'"),
                                makeLineCont())),
                    chain(states,
                          makeStrPrefix(),
                          newArcPair(states, '"'),
                          any(states,
                              notGroupStr(states, '\r\n"\\')),
                          any(states,
                              chain(states,
                                    newArcPair(states, "\\"),
                                    newArcPair(states, DEFAULT),
                                    any(states,
                                        notGroupStr(states, '\r\n"\\')))),
                          group(states,
                                newArcPair(states, '"'),
                                makeLineCont())))
    triple = chain(states,
                   makeStrPrefix(),
                   group(states,
                         chainStr(states, "'''"),
                         chainStr(states, '"""')))
    pseudoExtras = group(states,
                         makeLineCont(),
                         makeComment(),
                         triple)
    pseudoToken = chain(states,
                        makeWhitespace(),
                        group(states,
                              newArcPair(states, EMPTY),
                              pseudoExtras, number, funny, contStr, name))
    dfaStates, dfaAccepts = nfaToDfa(states, *pseudoToken)
    return DFA(dfaStates, dfaAccepts)

# ______________________________________________________________________

def makePyEndDFAMap ():
    states = []
    single = chain(states,
                   any(states, notGroupStr(states, "'\\")),
                   any(states,
                       chain(states,
                             newArcPair(states, "\\"),
                             newArcPair(states, DEFAULT),
                             any(states, notGroupStr(states, "'\\")))),
                   newArcPair(states, "'"))
    singleDFA = DFA(*nfaToDfa(states, *single))
    states = []
    double = chain(states,
                   any(states, notGroupStr(states, '"\\')),
                   any(states,
                       chain(states,
                             newArcPair(states, "\\"),
                             newArcPair(states, DEFAULT),
                             any(states, notGroupStr(states, '"\\')))),
                   newArcPair(states, '"'))
    doubleDFA = DFA(*nfaToDfa(states, *double))
    states = []
    single3 = chain(states,
                    any(states, notGroupStr(states, "'\\")),
                    any(states,
                        chain(states,
                              group(states,
                                    chain(states,
                                          newArcPair(states, "\\"),
                                          newArcPair(states, DEFAULT)),
                                    chain(states,
                                          newArcPair(states, "'"),
                                          notChainStr(states, "''"))),
                              any(states, notGroupStr(states, "'\\")))),
                    chainStr(states, "'''"))
    single3DFA = NonGreedyDFA(*nfaToDfa(states, *single3))
    states = []
    double3 = chain(states,
                    any(states, notGroupStr(states, '"\\')),
                    any(states,
                        chain(states,
                              group(states,
                                    chain(states,
                                          newArcPair(states, "\\"),
                                          newArcPair(states, DEFAULT)),
                                    chain(states,
                                          newArcPair(states, '"'),
                                          notChainStr(states, '""'))),
                              any(states, notGroupStr(states, '"\\')))),
                    chainStr(states, '"""'))
    double3DFA = NonGreedyDFA(*nfaToDfa(states, *double3))
    return {"'" : singleDFA,
            '"' : doubleDFA,
            "'''": single3DFA,
            '"""': double3DFA}

# ______________________________________________________________________

def output(name, dfa_class, dfa):
    import textwrap
    i = 0
    for line in textwrap.wrap(repr(dfa.accepts), width = 50):
        if i == 0:
            print "accepts =", line
        else:
            print "          ", line
        i += 1
    import StringIO
    print "states = ["
    for numstate, state in enumerate(dfa.states):
        print "    #", numstate
        s = StringIO.StringIO()
        i = 0
        for k, v in sorted(state.items()):
            i += 1
            if k == '\x00default':
                k = "automata.DEFAULT"
            else:
                k = repr(k)
            s.write(k)
            s.write('::')
            s.write(repr(v))
            if i < len(state):
                s.write(', ')
        s.write('},')
        i = 0
        if len(state) <= 4:
            text = [s.getvalue()]
        else:
            text = textwrap.wrap(s.getvalue(), width=36)
        for line in text:
            line = line.replace('::', ': ')
            if i == 0:
                print '    {' + line
            else:
                print '     ' + line
            i += 1
    print "    ]"
    print "%s = automata.%s(states, accepts)" % (name, dfa_class)
    print

def main ():
    print "# THIS FILE IS AUTOMATICALLY GENERATED BY gendfa.py"
    print "# DO NOT EDIT"
    print "# TO REGENERATE THE FILE, RUN:"
    print "#     python gendfa.py > dfa_generated.py"
    print
    print "from pypy.interpreter.pyparser import automata"
    pseudoDFA = makePyPseudoDFA()
    output("pseudoDFA", "DFA", pseudoDFA)
    endDFAMap = makePyEndDFAMap()
    output("double3DFA", "NonGreedyDFA", endDFAMap['"""'])
    output("single3DFA", "NonGreedyDFA", endDFAMap["'''"])
    output("singleDFA", "DFA", endDFAMap["'"])
    output("doubleDFA", "DFA", endDFAMap['"'])

# ______________________________________________________________________

if __name__ == "__main__":
    main()
