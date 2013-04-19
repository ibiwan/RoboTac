#!/usr/bin/env python
import sys, re

## Validates grammars in simplified BNF: 

## * Use multiple entries to encode alternation.  
## * EBNF [] and {} structures are not supported.
## * Nonterminals must each have at least one production.  
## * Nerminals must be wrapped in double quotes.  
## * Productions end with a period, and cannot span multiple lines.
## * All symbols must be separated by whitespace.
## * Empty productions must use the terminal "epsilon" (with quotes)
## * Left-Recursive productions are not supported.

## Example productions:      
##   funcdef -> "func" typename identifier parmblk .
##   parmblk -> "(" formalparams ")" "=" block .

## Correctness: testing the first two in separate blocks for clarity; third is irrelevant to non-E BNF
# A. term0 | term1  :  The terms must not have any common start symbols.
# B. fac0 fac1  :  If fac0 contains the empty sequence, then the factors must not have any common start symbols.
# C. [exp] or {exp}  :  The sets of start symbols of exp and of symbols that may follow K must be disjoint.

epsilon = '"epsilon"'
EOF = '"end-of-file"'
grammar = dict()
startSym = None

class symbolRules:
	def __init__(self):
		self.productions = list()
		self.first_set   = set()
		self.follow_set  = set()
		self.nullable    = False

def isTerminal(symbol):
	return re.match(r"\".*?\"", symbol)

def isEmpty(prod):
	return len(prod) == 1 and prod[0] == epsilon

def IsNullable(symbol):
	if symbol == epsilon:  return True
	if isTerminal(symbol): return False
	return grammar[symbol].nullable
				
def AllNullable(chain):
	return all(IsNullable(s) for s in chain)

def FirstOfChain(chain): # [Y1, Y2, ..., Yk]
	if not len(chain): return set()
	first1 = FirstOfSymbol(chain[0])
	if not epsilon in first1: return first1
	ret = (first1 - set(epsilon)) | FirstOfChain(chain[1:]) # union
	if all(epsilon in FirstOfSymbol(Y) for Y in chain): 
		ret.add(epsilon)
	return ret

def FirstOfSymbol(symbol):
	if isTerminal(symbol): return set([symbol])
	ret = set()
	if symbol in grammar:
		for prod in grammar[symbol].productions:
			if isEmpty(prod): grammar[symbol].first_set.add(prod[0])
			else:             ret |= FirstOfChain(prod) # union
 	return ret

def FIRST(symbol):
	if symbol == epsilon or not symbol in grammar: return set()
	return grammar[symbol].first_set

def FOLLOW(symbol):
	if symbol == epsilon or not symbol in grammar:  return set()
	return grammar[symbol].follow_set

def UnifyFollowSets(syma, setb):
	seta = FOLLOW(syma)
	newset = seta | setb
	if syma == epsilon or seta == newset:
		return False
	grammar[syma].follow_set = newset
	return True

## Read Productions from input
for line in sys.stdin:
	if line.strip() == "": continue
	match = re.search(r"^(\w+)\s+->\s*(.*?)\s*\.\s*$", line)
	if not match:
		print "ERROR: badly-formed BNF line: " + line; continue
	symbol = match.group(1)
	prod = re.split(r"\s+", match.group(2))
	if len(prod) and prod[0] == symbol:
		print "ERROR: left-recursive production"; continue
	if not startSym:          startSym = symbol
	if symbol != epsilon and not symbol in grammar: 
		grammar[symbol] = symbolRules()
	for s in prod:
		if s != epsilon and not s in grammar:
			grammar[s] = symbolRules()
	grammar[symbol].productions.append(prod)
		

## Make sure all nonterminals are defined
for symbol in grammar.keys():
	for prod in grammar[symbol].productions:
		for subsym in prod:
			if not isTerminal(subsym) and subsym not in grammar:
				print "ERROR: undefined nonterminal: " + subsym

## Print Productions
print "PRODUCTIONS:"
for symbol in grammar.keys():
	print symbol
	for prod in grammar[symbol].productions:
		print " "*(15) + " -> " + str(prod)

## Check Nullability
changesMade = True
while changesMade:
	changesMade = False
	for symbol in grammar.keys():
		if not grammar[symbol].nullable:
			for prod in grammar[symbol].productions:
				if			len(prod) == 0 \
						or (len(prod) == 1 and prod[0] == epsilon) \
						or AllNullable(prod):
					grammar[symbol].nullable = True
					changesMade = True

## Print Nullability
print "NULLABLE SYMBOLS:"
for symbol in grammar.keys():
	if grammar[symbol].nullable: print symbol

## Calculate First Sets
for symbol in grammar.keys():
	grammar[symbol].first_set = FIRST(symbol) | FirstOfSymbol(symbol) # union

## Print First Sets
print "FIRST SETS:"
for symbol in grammar.keys():
	print "FS<" + symbol + ">:" + " "*(20 - len(symbol)) + str(FIRST(symbol))

## A. Make sure all First Sets of productions for a given symbol are disjoint
for symbol in grammar.keys():
	for p1 in grammar[symbol].productions:
		for p2 in grammar[symbol].productions:
			if p1 != p2 and len(FirstOfChain(p1) & FirstOfChain(p2)): # intersection
				print "WARNING: uniqueness conflict for " + symbol + " between " + str(p1) + " and " + str(p2)

## B. Make sure all concatenated symbols within a production have disjoint First Sets
for symbol in grammar.keys():
	for prod in grammar[symbol].productions:
		if isEmpty(prod): continue
		s1 = prod[0]
		for s2 in prod[1:]: # examine all consecutive pairs
			if isTerminal(s1) or isTerminal(s2): continue
			if epsilon in grammar[s1].productions:
				f1 = FirstOfSymbol(s1); f2 = FirstOfSymbol(s2)
				if len(f1 & f2): # intersection
					print "WARNING: uniqueness conflict for " + symbol + " in production " + prod
					print "\t" + f1; print "\t" + f2
			s1 = s2 # update pair 'afore loopin'

## C. Irrelevant (only for Extended BNF, not handled here)

## Build follow sets (Per Appel 2004)
if startSym: 
	grammar[startSym].follow_set.add(EOF)
changesMade = True
while changesMade:
	changesMade = False
	for symbol in grammar.keys():
		for prod in grammar[symbol].productions:
			k = len(prod)
			for i in range(k):
				if i == k-1 or AllNullable(prod[i+1:k]):
					changesMade = UnifyFollowSets(prod[i], FOLLOW(symbol))
				for j in range(i+1, k):
					if i + 1 == j or AllNullable(prod[i+1:j]):
						changesMade = UnifyFollowSets(prod[i], FIRST(prod[j]) - set([epsilon]))
						
## Print Follow Sets
print "FOLLOW SETS:"
for symbol in grammar.keys():
	if grammar[symbol].follow_set:
		print "FolS<" + symbol + ">:" + " "*(18 - len(symbol)) + str(FOLLOW(symbol))

