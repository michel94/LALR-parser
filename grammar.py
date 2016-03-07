
def isBlank(s):
	for i in s:
		if not (i == '\n' or i == '\r' or i == ' '):
			return False
	return True

class Grammar:
	def __init__(self, terminals, rules, semantic=None):
		self.terminals = terminals
		self.productions = {}
		self.nonterminals = []
		self.assoc = None
		self.precedence = None
		self.annotatedRules = {}
		i = 0

		if semantic != None:
			for rule in rules:
				self.annotatedRules[rule] = semantic[i]
				i+=1


		self.rules = rules
		for rule in rules:
			if rule[0] not in self.productions:
				self.productions[rule[0]] = []
			self.productions[rule[0]].append(rule[1])

		for i in self.productions:
			if i not in self.nonterminals:
				self.nonterminals.append(i)

		self._first = {}
		for s in self.productions:
			self._first[s] = None

		for s in self.productions:
			if self._first[s] == None:
				self.FIRST([s], set())


	def FIRST(self, rule, stack):
		if len(rule) == 0:
			return {None}
		if rule[0] in stack:
			return set()
		total = set()
		if rule[0] in self.terminals:
			return {rule[0]}
		

		total = set()
		s2 = stack | {rule[0]}
		#print(self.productions, rule[0])
		for p in self.productions[rule[0]]:
			total |= self.FIRST(p, s2)

		self._first[rule[0]] = total | set()

		if None in total and len(rule) > 1:
			res = self.FIRST(rule[1:], stack)
			total |= res
			if None not in res:
				total.remove(None)

		return total

	def setAssoc(self, assoc):
		self.assoc = assoc

	def setPrecedence(self, precedence):
		self.precedence = precedence



def readGrammar(f, semantic=None):
	f = open(f)
	lines = f.readlines()
	terminals = lines[0].split()
	terminals.append('$')
	lines = lines[1:]

	operatorPrecedence = [] # pair of tuples, the first element has higher precedence
	operatorAssoc = {} # maps each operator to a string, with left or right

	rules = []
	for line in lines:
		if isBlank(line):
			continue

		special = line.split()
		if special[0][0] == '%':
			if special[0] == '%left' or special[0] == '%right':
				r = special[0][1:]
				for op in special[1:]:
					operatorAssoc[op] = r
			if special[0] == '%priority':
				special.pop(0)
				for op1 in range(len(special)):
					for op2 in range(op1+1, len(special)):
						operatorPrecedence.append((special[op1], special[op2]))
		else:
			left, right = line.split('->')
			left = left.strip()
			r = right.split('|')


			for prod in r:
				l = prod.split()
				l = [i for i in l if i != 'eps']
				rules.append( (left, tuple(l)) )

	#print(operatorPrecedence, operatorAssoc)

	#print(terminals, rules)
	g = Grammar(terminals, rules, semantic=semantic)
	g.setPrecedence(operatorPrecedence)
	g.setAssoc(operatorAssoc)
	return g

