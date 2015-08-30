import os
from ayrton.parser.pyparser import parser, pytoken, metaparser

class PythonGrammar(parser.Grammar):

    KEYWORD_TOKEN = pytoken.python_tokens["NAME"]
    TOKENS = pytoken.python_tokens
    OPERATOR_MAP = pytoken.python_opmap

def _get_python_grammar():
    here = os.path.dirname(__file__)
    fp = open(os.path.join(here, "data", "Grammar3.3"))
    try:
        gram_source = fp.read()
    finally:
        fp.close()
    pgen = metaparser.ParserGenerator(gram_source)
    return pgen.build_grammar(PythonGrammar)


python_grammar = _get_python_grammar()

class _Tokens(object):
    pass
for tok_name, idx in pytoken.python_tokens.items():
    setattr(_Tokens, tok_name, idx)
tokens = _Tokens()

class _Symbols(object):
    pass
for sym_name, idx in python_grammar.symbol_ids.items():
    setattr(_Symbols, sym_name, idx)
syms = _Symbols()

del _get_python_grammar, _Tokens, tok_name, sym_name, idx
