( +)return ast\.(.*)\((.*), (.*)\.get_lineno\(\), (.*)\.get_col_offset\(\)\)
\1new_node = ast.\2(\3)\n\1new_node.lineno = \4.lineno\n\1new_node.col_offset = \5.col_offset\n\1return new_node

( +)return ast\.(.*)\((.*)\.get_lineno\(\), (.*)\.get_col_offset\(\)\)
\1new_node = ast.\2()\n\1new_node.lineno = \3.lineno\n\1new_node.col_offset = \4.col_offset\n\1return new_node

ast.Load,
ast.Load(),

([a-z_]+)\.num_children\(\)
len(\1.children)

([a-z_]+)\.get_child\((.+)\)
\1.children[\2]

([a-z_]+)\.get_value\(\)
\1.value
