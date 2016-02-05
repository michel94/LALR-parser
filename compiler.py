
class Token:
	def __init__(self, type, *value):
		self.type = type
		self.value = value

	def isTerminal(self):
		return True

	def __repr__(self):
		return self.type

class Rule:
	def __repr__(self):
		s = "<" + self.name + ">" + " -> "
		for i in self.right:
			if i == None:
				s += " Eps"
			else:
				s += " " + "<" + i + ">"
		return s

	def __init__(self, name, right):
		self.name = name
		self.right = right

class Grammar:
	def __init__(self, terminals, rules):
		self.terminals = terminals
		self.productions = {}
		self.nonterminals = []

		self.rules = rules
		for rule in rules:
			if rule.name not in self.productions:
				self.productions[rule.name] = []
			self.productions[rule.name].append(rule.right)

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
			return set()
		if rule[0] in stack:
			return set()
		total = set()
		if rule[0] in self.terminals:
			return {rule[0]}
		

		total = set()
		s2 = stack | {rule[0]}
		for p in self.productions[rule[0]]:
			total |= self.FIRST(p, s2)

		self._first[rule[0]] = total | set()

		if None in total and len(rule) > 1:
			res = self.FIRST(rule[1:], stack)
			total |= res
			if None not in res:
				total.remove(None)

		return total

nodeCounter = 0

def printNode(gNode):
	nodeId = gNode.id
	node = gNode.data

	print("Node #" + str(nodeId))
	
	for prod in node:
		l = "".join([i if i != None else 'Eps' for i in prod[1]])
		r = "".join([i if i != None else 'Eps' for i in prod[2]])
		la = '|'.join([i if i != None else 'Eps' for i in prod[3]])
		print(prod[0], '->', l + '.' + r, ',', la)
	print()


class GraphNode:
	def __init__(self):
		self.transitions = {}
		self.data = None
		self.id = None

	def addNeigh(self, symbol, gNode):
		self.transitions[symbol] = gNode

	def addData(self, data):
		self.data = data

class LALRParser:
	def __init__(self, grammar, start):
		if not start:
			self.start = "S"
		else:
			self.start = start
		self.grammar = grammar

		self.graphNodes = {}
		self.nodeCount = 0
		self.rowCount = 0

		self.ruleDict = {}
		self.invertedRuleDict = {}
		ind = 1
		for symbol, rules in self.grammar.productions.items():
			for rule in rules:
				t = self.hashRule(symbol, rule)
				self.ruleDict[t] = ind
				ind += 1

		self.mergedNodes = {}
		self.table = None
		self.createParser()

	def createParser(self):
		node1 = []
		for right in self.grammar.productions[self.start]:
			node1.append((self.start, [], right, {"$"}) )
			
		graph = self.expand(node1)
		self.findNodesToMerge(graph, [])
		self.table = [{i:[] for i in self.grammar.terminals + self.grammar.nonterminals} for j in range( len(self.mergedNodes) )]
		self.createTable(graph, [])
		self.printTable()

		self.invertedRuleDict = {v:k for k, v in self.ruleDict.items()}

	def getNextNodeId(self):
		a = self.nodeCount
		self.nodeCount += 1
		return a

	def hashRule(self, symbol, right):
		return (symbol, tuple(right) )

	def getLR0(self, node):
		s = set()
		for rule in node:
			s.add( (rule[0], tuple(rule[1]), tuple(rule[2])) )

		return frozenset(s)

	def findNodesToMerge(self, gNode, vis):
		if gNode in vis:
			return
		vis.append(gNode)

		m = self.getLR0(gNode.data)
		if m not in self.mergedNodes:
			self.mergedNodes[m] = gNode
			gNode.rowId = self.rowCount
			self.rowCount += 1
		else:
			gNode.rowId = self.mergedNodes[m].rowId

		
		for tr in gNode.transitions:
			self.findNodesToMerge(gNode.transitions[tr], vis)


	def createTable(self, gNode, vis):
		if gNode in vis:
			return
		vis.append(gNode)

		for tr in gNode.transitions:
			nNode = gNode.transitions[tr]
			nId = nNode.rowId

			cell = self.table[gNode.rowId][tr]
			if tr in self.grammar.terminals:
				if ('shift', nId) not in cell:
					cell.append(('shift', nId))
			else:
				if ('goto', nId) not in cell:
					cell.append(('goto', nId))

			self.createTable(nNode, vis)

		for rule in gNode.data:
			if len(rule[2]) == 0: # finished production, reduce it
				t = self.hashRule(rule[0], rule[1])
				ind = self.ruleDict[t]

				for la in rule[3]:
					self.table[gNode.rowId][la].append(('reduce', ind))

	def printTable(self):
		print('\t' + '\t'.join(self.grammar.terminals + self.grammar.nonterminals))
		id = 0
		for row in self.table:
			l = []
			for k in self.grammar.terminals + self.grammar.nonterminals:
				item = []
				for i in row[k]:
					if len(i) == 0:
						item.append('')
					elif i[0] == 'shift':
						item.append('S' + str(i[1]))
					elif i[0] == 'reduce':
						item.append('R' + str(i[1]))
					else:
						item.append(str(i[1]))
				item = '/'.join(item)
				l.append(item)
			print(str(id) + ':\t' + '\t'.join(l))

			id += 1


	def advance(self, prod):
		la = self.grammar.FIRST(prod[2][1:], set())
		if len(la) == 0 or None in la:
			la |= prod[3]

		right = []
		if len(prod[2]) == 1:
			right = []
		else:
			right = prod[2][1:]

		return [prod[0], prod[1] + [prod[2][0]], right, prod[3] | set()]

	def expandRule(self, toExpand, expanded, right, lookahead):
		if len(right) > 0 and right[0] not in self.grammar.terminals:
			newLA = self.grammar.FIRST(right[1:], set())
			if len(newLA) == 0 or None in newLA:
				newLA |= lookahead

			if right[0] in expanded:
				return

			if right[0] not in toExpand:
				toExpand[right[0]] = set()
			toExpand[right[0]] |= newLA

			#print(toExpand)

	def expand(self, node):
		graphNode = GraphNode()
		toExpand = {} # dict that maps closure symbol to look-ahead symbols set
		expanded = set()

		for rule in node:
			symbol, left, right, lookahead = rule
			self.expandRule(toExpand, expanded, right, lookahead)

		while len(toExpand) > 0:
			symbol, lookahead = pop(toExpand)

			if symbol not in expanded:
				for right in self.grammar.productions[symbol]:
					node.append((symbol, [], right, lookahead))
					self.expandRule(toExpand, expanded, right, lookahead)

			expanded.add(symbol)

		transitions = {}
		for prod in node:
			if len(prod[2]) > 0:
				if prod[2][0] not in transitions:
					transitions[prod[2][0]] = []
				transitions[prod[2][0]].append(self.advance(prod))


		nodeHash = self.hashNode(node)
		if nodeHash in self.graphNodes:
			return self.graphNodes[nodeHash]

		graphNode.id = self.getNextNodeId()
		graphNode.addData(node)
		self.graphNodes[nodeHash] = graphNode

		printNode(graphNode)

		for tr in transitions:
			print('on', tr)
			gNode = self.expand(transitions[tr])
			graphNode.addNeigh(tr, gNode)

		return graphNode

	def hashNode(self, node):
		s = []
		for i in node:
			s.append((tuple(i[0]), tuple(i[1]), tuple(i[2]), tuple(i[3])))
		return tuple(s)

	def parse(self, inp):
		queue = []
		queue.append(0)
		
		t = inp[0]
		inp.pop(0)

		solved = False

		while True:
			#print(queue, t.type)

			op = self.table[queue[-1]][t.type]
			if len(op) > 1:
				print('conflict')
				break
			op = op[0]

			#print(op)
			if op[0] == 'shift':
				queue.append(t)
				queue.append(op[1])

				t = inp[0]
				inp.pop(0)
			if op[0] == 'reduce':
				ruleInd = op[1]
				rule = self.invertedRuleDict[ruleInd]
				symbol, prod = rule
				n = len(prod) * 2
				
				popped = queue[-n:]
				queue = queue[:-n]

				children = [popped[i] for i in range(len(popped)) if i%2 == 0]
				node = TreeNode(symbol, children)
				queue.append(node)
				r = queue[-2]
				c = queue[-1].type
				if len(queue) >= 2 and queue[-2] == 0 and queue[-1].type == 'S': # TODO: Fix this
					solved = True
					break
				queue.append(self.table[r][c][0][1])


		tree = queue[-1]
		return tree

def pop(d):
	for i in d:
		s = (i, d[i])
		del d[i]
		return s

def isBlank(s):
	for i in s:
		if not (i == '\n' or i == '\r' or i == ' '):
			return False
	return True

def readGrammar(f):
	f = open(f)
	lines = f.readlines()
	terminals = lines[0].split()
	terminals.append('$')
	lines = lines[1:]

	rules = []
	for line in lines:
		if isBlank(line):
			continue

		left, right = line.split('->')
		left = left.strip()
		r = right.split('|')


		for prod in r:
			l = prod.split()
			l = [i for i in l if i != 'eps']
			rules.append( Rule(left, l) )

	#print(terminals, rules)
	return Grammar(terminals, rules)


g = readGrammar("grammar1.txt")
parser = LALRParser(g, "S")


class TreeNode(Token):
	def __init__(self, type, children):
		self.type = type
		self.children = children

	def isTerminal(self):
		return False

	def __repr__(self):
		return "Node("  + self.type + ')'

	def printTree(self, depth):
		print('  ' * depth + self.type)
		for c in self.children:
			if c.isTerminal():
				print('  ' * (depth+1) + c.type)
			else:
				c.printTree(depth+1)


inp = [Token('a', 3), Token('a', 5), Token('b', 4), Token('b', 1), Token('$')]
S = parser.parse(inp)
S.printTree(0)

