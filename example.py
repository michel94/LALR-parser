from parser import Parser, GenericLexer, LexToken as LT, Token

LT.Add.name = '+'
LT.Mul.name = '*'
LT.Eq.name  = '='
LT.SemiColon.name = ';'

class Lexer(GenericLexer):
	name='langLexer'
	tokens = {
		'root': [
			(r'[a-zA-Z]+', LT.Id),
			(r'[0-9]+(\.[0-9]+)?', LT.Num),
			(r'\+', LT.Add),
			(r'\*', LT.Mul),
			(r'=', LT.Eq),
			(r';', LT.SemiColon)
		]
	}

data = open('tests/testOps.lang', 'r').read()
tokens = Lexer().parseString(data)
print(tokens)

parser = Parser()
#try:
parser.loadGrammar('tests/yaccTestOps.txt', ['Id', 'Num', '=', '*', '+', '$', ';'])
#codeInp = [Token('Id', 'var'), Token('='), Token('Num', 3), Token('+'), Token('Num', 5), Token('*'), Token('Num', 8), Token(';'), Token('$')]
tree = parser.parseTokens(tokens)
print('tree', tree)
#except InvalidGrammar as e:
	#print(e)
