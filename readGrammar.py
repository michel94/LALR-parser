import sys, re
from pygments.lexer import RegexLexer
from pygments.token import *
from pygments.token import Token as PygToken

from compiler import *

inputBuffer = sys.stdin.read()

EOF = -1

def see():
	global inputBuffer
	if len(inputBuffer) == 0:
		return EOF
	return inputBuffer[0]

def pick():
	global inputBuffer
	if len(inputBuffer) == 0:
		return EOF
	c = inputBuffer[0]
	inputBuffer = inputBuffer[1:]
	return c

def readStr(term):
	s = ""
	s += pick()
	while True:
		c = pick()
		s += c
		if c == term and s[-1] != '\\':
			return s

def readCode():
	code = ""
	code += pick()
	while True:
		if see() == '\'':
			code += readStr('\'')
		if see() == '\"':
			code += readStr('\"')
		if see() == '}':
			code += pick()
			return code
		code += pick()


class CodeHandler:
	def __init__(self):
		self.code = []
	def readCode(self):
		self.code.append(readCode())
		return '«' + str(len(self.code)-1) + '»'

	def getCode(self):
		return self.code

ind = 0
def f(s):
	global ind
	ind = ind+1
	return "«STRING" + str(ind) + "»"

#print('inputBuffer:', inputBuffer, 'END')
inputBuffer = re.sub("\"([^\"\n\\]|\\[^'\n]|(\\[\\\"\'nt])*)*\\?", f, inputBuffer) # TODO: Fix with proper string regex
#inputBuffer = re.sub('"([^\"])*"', f, inputBuffer)
print('inputBuffer:', inputBuffer, 'END')

codeHandler = CodeHandler()
annotatedRules = ''
while True:
	if see() == EOF:
		break
	elif see() == '{':
		annotatedRules += codeHandler.readCode()
	else:
		annotatedRules += pick()


#print(annotatedRules, codeHandler.getCode())
#print(annotatedRules)

Arrow = PygToken.Arrow
VertSlash = PygToken.VertSlash
Code = PygToken.Code

class Lexer(RegexLexer):
	name='yaccLexer'
	tokens = {
		'root': [
			(r'->', Arrow),
			(r'\|', VertSlash),
			(r'«[0-9]+»', Code),
			(r'[a-zA-Z]+', Literal),
			(r'\+|\-|\=|;|\.|~|\*|/|\\|:', Literal),
			(r'[ \n]+', Whitespace)
		]
	}


names = {Arrow: 'Arrow', Code: 'Code', VertSlash: 'VertSlash', Literal: 'Token'}

lexer = Lexer()
unprocessed_tokens = lexer.get_tokens_unprocessed(annotatedRules)
tokens = []
for i in unprocessed_tokens:
	if i[1] in names:
		name = names[i[1]]
		tokens.append(Token(name, i[2]))

tokens.append(Token('$'))

class GrammarNode(Token):
	def __init__(self, type, data):
		self.type = type
		self.data = data

	def isTerminal(self):
		return False

	def __repr__(self):
		return "Node("  + self.type + ')'


rules = []
semanticRules = []

def createRule(symbol, productions):
	
	for p in productions:
		print()
		rules.append( (symbol.value, tuple([i.value for i in p[0]]) ))
		codeId = int(p[1].value[1:-1])
		semanticRules.append(codeHandler.getCode()[codeId][1:-1])

def listAppend(l, it):
	l.append(it)
	return l

def pack(a, b):
	return (a, b)

semantic = [
	CHILD(0),
	[createRule, CHILD(1), CHILD(3)], None,
	[listAppend, CHILD(0), CHILD(1)],
	[listAppend, CHILD(0), CHILD(1)], [],
	[pack, CHILD(0), CHILD(1)],
	CHILD(0), None,
	[listAppend, CHILD(0), CHILD(1)], [CHILD(0)]
]
g = readGrammar("yaccRules.grammar", semantic=semantic)
parser = LALRParser(g, "S")


print(tokens)
parser.parse(tokens)

print()
print('rules', rules)


codeInp = [Token('Id', 'var'), Token('='), Token('Num', 3), Token('+'), Token('Num', 5), Token('-'), Token('Num', 8), Token(';'), Token('$')]

print('semanticRules', semanticRules)
g2 = Grammar(['Id', 'Num', '=', '-', '+', '$', ';'], rules, semanticRules)
languageParser = LALRParser(g2, 'S', evalSemantic=True)
s = languageParser.parse(codeInp)
print(s)


