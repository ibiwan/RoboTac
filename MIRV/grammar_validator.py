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
grammar = dict()

class symbolRules:
	def __init__(self):
		self.productions = list()
		self.first_set = set()
		self.follow_set = set()

def isTerminal(symbol):
	return re.match(r"\".*?\"", symbol)

def isEmpty(prod):
	return len(prod) == 1 and prod[0] == epsilon

def FirstOfChain(chain): # [Y1, Y2, ..., Yk]
	if not len(chain): return set()
	first1 = FirstOfSymbol(chain[0])
	if not epsilon in first1:
		return first1
	ret = (first1 - set(epsilon)) | FirstOfChain(chain[1:]) # union
	if all(epsilon in FirstOfSymbol(Y) for Y in chain): 
		ret.add(epsilon)
	return ret

def FirstOfSymbol(symbol):
	ret = set()
	if isTerminal(symbol):
		ret.add(symbol)
		return ret
	if symbol in grammar:
		for prod in grammar[symbol].productions:
			if isEmpty(prod):
				grammar[symbol].first_set.add(prod[0])
			else:
				ret |= FirstOfChain(prod) # union
 	return ret

## Read Productions from input
for line in sys.stdin:
	if line.strip() == "": continue
	match = re.search(r"^(\w+)\s+->\s*(.*?)\s*\.\s*$", line)
	if not match:
		print "ERROR: badly-formed BNF line: " + line
		continue
	symbol = match.group(1)
	prod = re.split(r"\s+", match.group(2))
	if len(prod) and prod[0] == symbol:
		print "ERROR: left-recursive production"
		continue
	if not symbol in grammar:
		grammar[symbol] = symbolRules()
	grammar[symbol].productions.append(prod)


## Make sure all nonterminals are defined
for symbol in grammar.keys():
	for prod in grammar[symbol].productions:
		for subsym in prod:
			if not isTerminal(subsym) and subsym not in grammar:
				print "ERROR: undefined nonterminal: " + subsym

## Calculate First Sets
for symbol in grammar.keys():
	grammar[symbol].first_set |= FirstOfSymbol(symbol) # union

## Print First Sets
for symbol in grammar.keys():
	print "FS<" + symbol + ">:" + " "*(20 - len(symbol)) + str(grammar[symbol].first_set)

## A. Make sure all First Sets of productions for a given symbol are disjoint
for symbol in grammar.keys():
	for p1 in grammar[symbol].productions:
		for p2 in grammar[symbol].productions:
			if p1 != p2 and len(FirstOfChain(p1) & FirstOfChain(p2)): # intersection
				print "WARNING: uniqueness conflict for " + symbol + " between " + str(p1) + " and " + str(p2)

## B. Make sure all concatenated symbols within a production are disjoint
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
					print "\t" + f1
					print "\t" + f2
			s1 = s2

## C. Irrelevant (only for Extended BNF, not handled here)

## check correctness of follow sets
