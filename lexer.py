from pygments.token import *
from pygments.token import _TokenType
from pygments.lexer import RegexLexer

from compiler import Token

class _LexToken(_TokenType):
	parent = None

	def __init__(self, *args):
		_TokenType.__init__(self, args)

	def __getattr__(self, val):
		if not val or not val[0].isupper():
			return tuple.__getattribute__(self, val)
		new = _LexToken(self + (val,))
		new.name = val
		setattr(self, val, new)
		self.subtypes.add(new)
		new.parent = self
		return new

	def getName(self):
		return self.name

LexToken = _LexToken()


class GenericLexer(RegexLexer):

	def parseString(self, data):
		l = self.get_tokens_unprocessed(data)
		tokens = []
		for i in l:
			tok = i[1]
			if issubclass(type(tok), _LexToken):
				tokens.append(Token(tok.getName(), i[2]))
		tokens.append(Token('$'))

		return tokens

	def _process_token(token):
		assert  issubclass(type(token), _TokenType) or callable(token), \
			'token type must be simple type or callable, not %r' % (token,)
		return token

	def get_tokens_unprocessed(self, text, stack=('root',)):
		"""
		Split ``text`` into (tokentype, text) pairs.

		``stack`` is the inital stack (default: ``['root']``)
		"""
		pos = 0
		tokendefs = self._tokens
		statestack = list(stack)
		statetokens = tokendefs[statestack[-1]]
		while 1:
			for rexmatch, action, new_state in statetokens:
				m = rexmatch(text, pos)
				if m:
					if action is not None:
						if issubclass(type(action), _TokenType):
							yield pos, action, m.group()
						else:
							for item in action(self, m):
								yield item
					pos = m.end()
					if new_state is not None:
						# state transition
						if isinstance(new_state, tuple):
							for state in new_state:
								if state == '#pop':
									statestack.pop()
								elif state == '#push':
									statestack.append(statestack[-1])
								else:
									statestack.append(state)
						elif isinstance(new_state, int):
							# pop
							del statestack[new_state:]
						elif new_state == '#push':
							statestack.append(statestack[-1])
						else:
							assert False, "wrong state def: %r" % new_state
						statetokens = tokendefs[statestack[-1]]
					break
			else:
				# We are here only if all state tokens have been considered
				# and there was not a match on any of them.
				try:
					if text[pos] == '\n':
						# at EOL, reset state to "root"
						statestack = ['root']
						statetokens = tokendefs['root']
						yield pos, Text, u'\n'
						pos += 1
						continue
					yield pos, Error, text[pos]
					pos += 1
				except IndexError:
					break

