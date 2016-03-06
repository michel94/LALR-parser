
from compiler import *

#['A', ['A', 'B', 'C'], make_node, [1, 3, 2]]

class Node:
	def __init__(self, type, *children):
		self.type = type
		self.children = children
	def __repr__(self):
		return 'Node(' + self.type + ')'

'''
semantic = [[CHILD(0)],
[Node, 'mul', CHILD(0), CHILD(2)],
[Node, 'add', CHILD(0), CHILD(2)],
[CHILD(0)]]
'''

g = readGrammar("grammar1.txt", semantic=None)
parser = LALRParser(g, "S")

#inp = [Token('a', 3), Token('a', 5), Token('b', 4), Token('b', 1), Token('$')]
'''
inp = [Token('a', 3), Token('b', 5), Token('b', 4), Token('a', 1), Token('$')]
S = parser.parse(inp)
S.printTree(0)
'''
#inp = [Token('int', 3), Token('+'), Token('int', 3), Token('+'), Token('int', 4), Token('*'), Token('int', 2), Token('$')]

inp = [Token('a'), Token('b'), Token('b'), Token('b'), Token('$')]
S = parser.parse(inp)

'''
def calc(t):
	if t.type == 'int':
		return t.value
	elif t.type == 'mul':
		return calc(t.children[0]) * calc(t.children[1])
	elif t.type == 'add':
		return calc(t.children[0]) + calc(t.children[1])
print(calc(S))
'''

print(S)


