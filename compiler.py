from grammar import *

#Semantic specific classes

class CHILD:
	def __init__(self, ind):
		self.index = ind

class Token:
	def __init__(self, type, *value):
		self.type = type
		self.value = None
		if len(value) == 1:
			self.value = value[0]

	def isTerminal(self):
		return True

	def __repr__(self):
		return 'Token(' + self.type + ')'


class InternalTree(Token):
	def __init__(self, type, data):
		self.type = type
		self.data = data

	def isTerminal(self):
		return False

	def __repr__(self):
		return "Node("  + self.type + ')'

nodeCounter = 0

def printNode(gNode):
	nodeId = gNode.id
	node = gNode.data

	print("Node #" + str(nodeId))
	
	for prod in node:
		l = " ".join([i if i != None else 'Eps' for i in prod[1]])
		r = " ".join([i if i != None else 'Eps' for i in prod[2]])
		la = ' | '.join([i if i != None else 'Eps' for i in prod[3]])
		print(prod[0], '->', l + ' . ' + r, ',', la)
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
	def __init__(self, grammar, start, evalSemantic=False):
		if not start:
			self.start = "S"
		else:
			self.start = start
		self.grammar = grammar

		self.graphNodes = {}
		self.nodeCount = 0
		self.rowCount = 0
		self.evalSemantic = evalSemantic

		# dictionaries to map rules with an index and vice-versa. used to handle reduce ids
		self.ruleDict = {} 
		self.invertedRuleDict = {}

		ind = 1
		for symbol, rules in self.grammar.productions.items():
			for rule in rules:
				t = self.hashRule(symbol, rule)
				self.ruleDict[t] = ind
				ind += 1

		self.mergedNodes = {} # map merged nodes (same LR(0) items) to ids
		self.table = None # parser table

		self.hasConflicts = False

		self.createParser() # generate parser, graph + table + compression

	def createParser(self):
		node1 = []
		for right in self.grammar.productions[self.start]:
			node1.append((self.start, [], right, {"$"}) )
			
		graph = self.expand(node1)
		self.findNodesToMerge(graph, [])

		nodeList = [ v for k, v in self.mergedNodes.items()]
		nodeList = sorted(nodeList, key=lambda node: node.id)

		self.table = [{i:[] for i in self.grammar.terminals + self.grammar.nonterminals} for j in range( len(nodeList) )]
		self.createTable(graph, [])

		self.invertedRuleDict = {v:k for k, v in self.ruleDict.items()}
		
		self.hasConflicts = self.fixConflicts()
		self.printTable()

	def fixConflicts(self):
		conflict = False
		for i in range(len(self.mergedNodes)):
			for j in self.grammar.terminals + self.grammar.nonterminals:
				if len(self.table[i][j]) > 1:
					l = self.table[i][j]
					if len(l) == 2:
						if l[0][0] == 'shift' or l[1][0] == 'shift': # shift-reduce, can be solved
							r = None
							s = None
							if l[0][1] == 'reduce':
								r = l[0]
								s = l[1]
							else:
								r = l[1]
								s = l[0]

							#print(self.invertedRuleDict[ r[1] ])
							if len(self.invertedRuleDict[ r[1] ][1] ) > 1:
								opReduce = self.invertedRuleDict[ r[1] ] [1][-2] # get r[1] (reduce index), then get second element (right part of the production), then get the operator
								opShift = j
								#print('reduce op', opReduce)

								if self.grammar.assoc != None and opReduce == opShift:
									if opReduce in self.grammar.assoc:
										if self.grammar.assoc[opReduce] == 'left':
											self.table[i][j] = r
										else:
											self.table[i][j] = s
										continue
								if self.grammar.precedence != None:
									if (opReduce, opShift) in self.grammar.precedence:
										self.table[i][j] = r
										continue
									elif (opShift, opReduce) in self.grammar.precedence:
										self.table[i][j] = s
										continue

							# TODO: Automatic shift, fix this
							self.table[i][j] = s
							continue

					conflict = True
					print('conflict not solved', self.table[i][j])
				elif len(self.table[i][j]) == 1:
					self.table[i][j] = self.table[i][j][0]
				else:
					self.table[i][j] = None

		return conflict

	def getNextNodeId(self):
		a = self.nodeCount
		self.nodeCount += 1
		return a

	def hashRule(self, symbol, right):
		return (symbol, tuple(right) )

	def hashLR0item(self, node): # create hashable element with all rules of a LR(0) item (ignoring lookaheads), useful to merge nodes
		s = set()
		for rule in node:
			s.add( (rule[0], tuple(rule[1]), tuple(rule[2])) )

		return frozenset(s)

	def hashLR1item(self, node): # create hashable element with all rules of a LR(0) item (ignoring lookaheads), useful to merge nodes
		s = set()
		for rule in node:
			s.add( (rule[0], tuple(rule[1]), tuple(rule[2]), tuple(rule[3])) )
		return frozenset(s)

	def findNodesToMerge(self, gNode, vis):
		if gNode in vis:
			return
		vis.append(gNode)

		m = self.hashLR0item(gNode.data)
		if m not in self.mergedNodes:
			self.mergedNodes[m] = gNode
			gNode.rowId = self.rowCount
			print('row:', self.rowCount, 'nodeId:', gNode.id)
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

				for la in rule[3] - {None}:
					cell = self.table[gNode.rowId][la]
					if ('reduce', ind) not in cell:
						cell.append(('reduce', ind))

	def printTable(self):
		print('\t' + '\t'.join([i[0:6] for i in self.grammar.terminals + self.grammar.nonterminals]))
		id = 0
		for row in self.table:
			l = []
			for k in self.grammar.terminals + self.grammar.nonterminals:
				item = []

				if row[k] != None:
					if not isinstance(row[k], list): # if row is not a list, iterate over a list with only one element
						r = [row[k]]
					else:
						r = row[k]

					for i in r:
						if len(i) == 0:
							item.append('')
						elif i[0] == 'shift':
							item.append('S' + str(i[1]))
						elif i[0] == 'reduce':
							item.append('R' + str(i[1]))
						else:
							item.append(str(i[1]))
					item = '/'.join(item)
				else:
					item = ''
				l.append(item)
			print(str(id) + ':\t' + '\t'.join(l))

			id += 1


	def advance(self, prod):
		# generate next node (move dot forward in all productions)
		right = []
		if len(prod[2]) == 1:
			right = []
		else:
			right = prod[2][1:]

		return [prod[0], prod[1] + [prod[2][0]], right, prod[3] | set()]

	def closure(self, rules, remainingSymbols, symbol, lookahead):
		for right in self.grammar.productions[symbol]:
			s = (symbol, tuple(right))
			
			#does this complete rule exist? if not, added it with lookahead
			if s in rules and len(lookahead - rules[s]) == 0: # rule exists, and lookahead is included in the existing one
				continue
			else: # rule doesn't exist, or existing lookahead doesn't include the new one 
				if s not in rules:
					rules[s] = set()
				rules[s] |= lookahead

				# apply closure to left most symbol of production?
				if len(right) > 0 and right[0] not in self.grammar.terminals:
					newLA = self.grammar.FIRST(right[1:], set())
					if len(newLA) == 0 or None in newLA:
						newLA |= lookahead

					nSymbol = right[0]
					if nSymbol not in remainingSymbols:
						remainingSymbols[nSymbol] = set()
					remainingSymbols[nSymbol] |= newLA


	def getLookahead(self, right, lookahead):
		la = self.grammar.FIRST(right[1:], set())
		if len(la) == 0 or None in la:
			la |= lookahead

		return la

	def expand(self, node):
		graphNode = GraphNode()
		remainingSymbols = {} # dict that maps closure symbol to look-ahead symbols set

		expanded = set() # (symbol, right, lookahead)

		# for current rules, get all symbols to apply closure and respective look-ahead
		for rule in node:
			symbol, left, right, lookahead = rule
			if len(right) > 0 and right[0] not in self.grammar.terminals:
				if right[0] not in remainingSymbols:
					remainingSymbols[right[0]] = set()
				remainingSymbols[right[0]] |= self.getLookahead(right, lookahead)

		# apply closure to all symbols, keep adding to the queue the left most symbols that belong to the new rules (or have new lookaheads)
		newRules = {}
		while len(remainingSymbols) > 0:
			symbol, lookahead = pop(remainingSymbols)
			self.closure(newRules, remainingSymbols, symbol, lookahead)

		for k in newRules:
			node.append([k[0], [], k[1], newRules[k]])

		# generate transitions for each production, joining together those for the same input symbol
		transitions = {}
		for prod in node:
			if len(prod[2]) > 0:
				if prod[2][0] not in transitions:
					transitions[prod[2][0]] = []
				transitions[prod[2][0]].append(self.advance(prod))

		# update graph node, making sure that there are no repeated nodes (same rules with same lookaheads)
		nodeHash = self.hashLR1item(node)
		if nodeHash in self.graphNodes:
			return self.graphNodes[nodeHash]

		graphNode.id = self.getNextNodeId()
		graphNode.addData(node)
		self.graphNodes[nodeHash] = graphNode

		printNode(graphNode)

		# recursively generate nodes connected to this one
		for tr in transitions:
			print('on', tr)
			gNode = self.expand(transitions[tr]) # will return an existing node if the generated node matches one
			graphNode.addNeigh(tr, gNode)

		return graphNode

	def getNodeData(self, node):
		if isinstance(node, InternalTree):
			return node.data
		else:
			return node

	def parse(self, inp):
		if self.hasConflicts:
			raise ValueError('Conflicts must be solved first!')

		queue = []
		queue.append(0)
		
		inputSize = len(inp)

		t = inp[0]
		inp.pop(0)

		solved = False

		while True:

			op = self.table[queue[-1]][t.type]
			#print(queue, t.type, op)
			
			if op == None:
				l = inputSize - len(inp)
				raise ValueError('Cannot parse input! Shifted ' + str(l) + ' tokens')

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
				
				if n > 0:
					popped = queue[-n:]
					queue = queue[:-n]
				else:
					popped = []

				children = [popped[i] for i in range(len(popped)) if i%2 == 0]
				
				data = None
				v = None
				if rule in self.grammar.annotatedRules:
					s = self.grammar.annotatedRules[rule]
					if self.evalSemantic:
						def childToken(n):
							return self.getNodeData(children[n])
						
						l = locals()
						r = exec(s, {}, l)
						data = l['v']
					else:
						if type(s) is list and len(s) > 0 and callable(s[0]):
							args = [self.getNodeData(children[i.index]) if isinstance(i, CHILD) else i for i in s[1:]]
							data = s[0](*args)
						elif not (type(s) is list):
							if isinstance(s, CHILD):
								data = self.getNodeData(children[s.index])
							else:
								data = s
						else:
							data = [self.getNodeData(children[i.index]) if isinstance(i, CHILD) else i for i in s]
				
				node = InternalTree(symbol, data)
				

				queue.append(node)
				r = queue[-2]
				c = queue[-1].type
				if len(queue) >= 2 and queue[-2] == 0 and queue[-1].type == 'S': # TODO: Fix this
					solved = True
					break
				queue.append(self.table[r][c][1])


		tree = queue[-1]
		return tree.data

def pop(d):
	for i in d:
		s = (i, d[i])
		del d[i]
		return s

