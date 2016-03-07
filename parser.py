
from pygments.token import _TokenType, Token as _PygToken
from lexer import GenericLexer, LexToken as LT, LexToken

from compiler import *

EOF = -1

class Buffer:
	def __init__(self, s):
		self.inputBuffer = s

	def see(self):
		if len(self.inputBuffer) == 0:
			return EOF
		return self.inputBuffer[0]
	
	def pick(self):
		if len(self.inputBuffer) == 0:
			return EOF
		c = self.inputBuffer[0]
		self.inputBuffer = self.inputBuffer[1:]
		return c

	def readStr(self, term):
		s = ""
		s += self.pick()
		while True:
			c = self.pick()
			s += c
			if c == term and s[-1] != '\\':
				return s

	def readCode(self):
		code = ""
		code += self.pick()
		while True:
			if self.see() == '\'':
				code += self.readStr('\'')
			if self.see() == '\"':
				code += self.readStr('\"')
			if self.see() == '}':
				code += self.pick()
				return code
			code += self.pick()


class CodeHandler:
	def __init__(self, inputBuffer):
		self.code = []
		self.inputBuffer = inputBuffer
	def readCode(self):
		self.code.append(self.inputBuffer.readCode())
		return '«' + str(len(self.code)-1) + '»'
	def getCode(self):
		return self.code


class YaccLexer(GenericLexer):
	name='yaccLexer'
	tokens = {
		'root': [
			(r'[a-zA-Z]+[ \n\t]+->', LT.Left),
			(r'\|', LT.VertSlash),
			(r'%[a-zA-Z]+', LT.Macro),
			(r'«[0-9]+»', LT.Code),
			(r'[a-zA-Z]+', LT.Token),
			(r'\+|\-|\=|;|\.|~|\*|/|\\|:', LT.Token),
		]
	}

class InvalidGrammar(Exception):
	def __init__(self):
		Exception.__init__(self, "InvalidGrammar: The grammar provided could not be parsed.")

class Parser():
	def __init__(self):
		self.lexicalRules = None
		self.inputFile = None
		self.rules = []
		self.semanticRules = []
		self.codeHandler = None
		self.precedence = []
		self.assoc = {}

		self.languageParser = None

		self.loadYaccParser()

	def loadYaccParser(self):

		def createRule(symbol, productions):
			symbol = symbol.value.split()[0]
			
			for p in productions:
				self.rules.append( (symbol, tuple([i.value for i in p[0]]) ))
				codeId = int(p[1].value[1:-1])
				self.semanticRules.append(self.codeHandler.getCode()[codeId][1:-1])

		def createMacro(macro, ops):
			macro = macro.value
			ops = [o.value for o in ops]
			if macro == '%priority':
				for op1 in range(len(ops)):
					for op2 in range(op1+1, len(ops)):
						self.precedence.append((ops[op1], ops[op2]))
			elif macro == '%right' or macro == '%left':
				m = macro[1:]
				for op in ops:
					self.assoc[op] = m
			else:
				print('Invalid macro ', macro)


		def listAppend(l, it):
			l.append(it)
			return l

		def pack(a, b):
			return (a, b)

		semantic = [
			CHILD(0),
			None, None,
			[createRule, CHILD(0), CHILD(1)], [createMacro, CHILD(0), CHILD(1)],
			[listAppend, CHILD(0), CHILD(1)],
			[listAppend, CHILD(0), CHILD(1)], [],
			[pack, CHILD(0), CHILD(1)],
			CHILD(0), None,
			[listAppend, CHILD(0), CHILD(1)], [CHILD(0)]
		]
		g = readGrammar("yaccRules.grammar", semantic=semantic)
		self.yaccParser = LALRParser(g, "S")

	def loadGrammar(self, filename, terminals):
		try:
			data = open(filename).read()
			#data = re.sub("\"([^\"\n\\]|\\[^'\n]|(\\[\\\"\'nt])*)*\\?", f, data) # TODO: Fix with proper string regex
			#print('inputBuffer:', data, 'END')
			inputBuffer = Buffer(data)

			self.codeHandler = CodeHandler(inputBuffer)
			annotatedRules = ''
			while True:
				if inputBuffer.see() == EOF:
					break
				elif inputBuffer.see() == '{':
					annotatedRules += self.codeHandler.readCode()
				else:
					annotatedRules += inputBuffer.pick()
			
			tokenNames = [LT.Left, LT.Code, LT.VertSlash, LT.Token, LT.Macro]

			lexer = YaccLexer()
			tokens = lexer.parseString(annotatedRules)

			self.yaccParser.parse(tokens)
			self.grammar = Grammar(terminals, self.rules, self.semanticRules)
			self.grammar.setPrecedence(self.precedence)
			self.grammar.setAssoc(self.assoc)
			self.languageParser = LALRParser(self.grammar, 'S', evalSemantic=True)
		
		except Exception as e:
			raise InvalidGrammar()

	def parseTokens(self, tokens=None):
		# TODO: with or without lexical analysis
		return self.languageParser.parse(tokens)

