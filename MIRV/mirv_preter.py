#!/usr/bin/env python
import lexer, sys

EOF = "end-of-file"
sym = None

varTypes = ["INT", "REAL", "ARRAY", "LIST", "STRING", "MATRIX"]
allTypes = varTypes + ["PROC", "FUNC"]
scopes = ["SET", "GLOBAL", "LET", "LOCAL"]
literals = ["INT", "REAL", "STRING"]

def nextsym():
	global sym
	try:
		sym = lex.next()
	except StopIteration as i:
		sym = (EOF, None)
	print sym

def error(expected):
	print "ERROR: expected " + expected + ", got " + sym[0]
	sys.exit("bailing -- no panic mode yet")

def consume(target, english):
	if (isinstance(target, list) and sym[0] in target) \
	    or sym[0] == target:
		ret = sym
		nextsym()
		return ret
	elif english: error(english)
	else: return None

def program():
	# -> definitions .
	# FIRST: "scope"
	# FOLLOW: "end-of-file"
	definitions()

def definitions():
	# -> definition definitions .
	# -> "epsilon" .
	# FIRST: "epsilon", "scope"
	# FOLLOW: "end-of-file"
	if sym[0] != EOF:
		definition()
		definitions()

def definition():
	# -> scope deftype .
	# FIRST: "scope"
	# FOLLOW: "end-of-file", ";", "scope"
	scope = consume(scopes, "scope symbol")[0]
	deftype(scope)

def deftype(defScope):
	# -> "func" funcdef .
	# -> "proc" procdef .
	# -> typename vardef .
	# FIRST: "func", "typename", "proc"
	# FOLLOW: "end-of-file", ";", "scope"
	if sym[0] == "FUNC":
		nextsym()
		funcdef(defScope)
	elif sym[0] == "PROC":
		nextsym()
		procdef(defScope)
	elif sym[0] in varTypes: #FUNC/PROC handled separately
		nextsym()
		vardef(defScope, sym[1])
	else: error("type specifier")

def funcdef(funcScope):
	# -> typename identifier "(" formalparams ")"  "=" block .
	# FIRST: "typename"
	# FOLLOW: "end-of-file", ";", "scope"
	funcReturnType = consume(varTypes, "variable type specifier")[0] # FUNC/PROC handled separately
	funcName = consume("ID", "identifier")[1]
	#print "function setup: ", funcScope, funcReturnType, funcName
	consume("LPAREN", "left parenthesis")
	formalparams()
	consume("RPAREN", "right parenthesis")
	consume("ASSIGN", "assignment")
	block()

def procdef(procScope):
	# -> identifier "(" formalparams ")"  "=" block .
	# FIRST: "("
	# FOLLOW: "end-of-file", ";", "scope"
	procName = consume("ID", "identifier")[1]
	consume("LPAREN", "left parenthesis")
	formalparams()
	consume("RPAREN", "right parenthesis")
	consume("ASSIGN", "assignment")
	block()

def vardef(varScope, varType):
	# -> identifier "=" expression ";" . 
	# FIRST: "typename"
	# FOLLOW: "end-of-file", ";", "scope"
	varName = consume("ID", "identifier")[1]
	consume("ASSIGN", "assignment")
	#expression()
	consume("SEMI", "semicolon")
	
def block():
	# -> "{" statements "}" . 
	# FIRST: "{"
	# FOLLOW: "}", "end-of-file", ";", "scope", "("
	consume("LBRACE", "left curly brace")
	statements()
	consume("RBRACE", "right curly brace")

def statements():
	# -> statement statements .
	# -> "epsilon" .
	# FIRST: "prebind", "prefixop", "set", "(", "identifier", "cond", "epsilon", 
	#        "call", "literal", "scope", "rpn", "return", "apply", "while"
	# FOLLOW: "}"
	if sym[0] in ["PREBIND", "PREFIXOP", "SET", "LPAREN", "ID", "COND", "CALL", "RPN", \
				  "RETURN", "APPLY", "WHILE"] + literals + scopes:
		# don't eat symbol; we don't use it here
		statement()
		statements()
	# epsilon: no "else"

def statement():
	# -> expression ";" 	FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# -> definition ";" 	FIRST: "scope"
	# -> kwstmt ";" 		FIRST: "while", "set", "rpn", "return", "cond", "call"
	# FIRST: "prebind", "prefixop", "set", "(", "identifier", "cond", 
	#        "call", "literal", "scope", "rpn", "return", "apply", "while"
	# FOLLOW: "prebind", "prefixop", "set", "apply", "(", "cond", "}", "while", 
	#         "literal", "scope", "rpn", "return", "identifier", "call"
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		expression()
		consume("SEMI", "semicolon")
	elif sym[0] in scopes:
		definition()
		consume("SEMI", "semicolon")
	elif sym[0] in ["WHILE", "SET", "RPN", "RETURN", "COND", "CALL"]:
		#kwstmt()
		consume("SEMI", "semicolon")
	else: error("statement (expression; or definition; or keyword statement;)")


#expression   -> term opterm .
#opterm       -> infixop expression .
#opterm       -> "epsilon" .
#term         -> literal .
#term         -> prebinding .
#term         -> indexable index .
#index        -> "[" expression "]" .
#index        -> "epsilon" .
#indexable    -> identifier .
#indexable    -> application .
#indexable    -> prefixop expression .
#indexable    -> "(" expression ")" .

def formalparams():
	# -> typename identifier moreformals .
	# -> "epsilon" .
	# FIRST: "epsilon", "typename"
	# FOLLOW: ")"
	found = consume(allTypes, None)
	if found: #epsilon: ok to not find
		paramType = found[0]
		paramName = consume("ID", "identifier")[1]
		#print "formal param: ", paramType, paramName
		moreformals()

def moreformals():
	# -> "," formalparams .
	# -> "epsilon" .
	# FIRST: "epsilon", ","
	# FOLLOW: ")"
	found = consume("COMMA", None)
	if found: formalparams() # epsilon: ok not to find

#formalparams -> typename identifier moreformals .
#formalparams -> "epsilon" .
#moreformals  -> "," formalparams .
#moreformals  -> "epsilon" .
#actualparams -> "@" identifier "=" expression moreactuals .
#actualparams -> expression moreactuals .
#actualparams -> "epsilon" .
#moreactuals  -> "," actualparams .
#moreactuals  -> "epsilon" .
#prebinding   -> "prebind" binding .
#binding      -> identifier actuals . 
#fkwbinding   -> fnkw actuals . 
#pkwbinding   -> prockw actuals . 
#actuals      -> "(" actualparams ")" . 
#kwstmt       -> "cond" "{" condelements "}" .
#kwstmt       -> "while" "(" expression ")" block .
#kwstmt       -> "set" identifier "=" expression .
#kwstmt       -> "rpn" rpnelements . 
#kwstmt       -> calling .
#kwstmt       -> "return" expression . 
#condelements -> "(" expression ")" block condelements .
#condelements -> "epsilon" .
#rpnelements  -> rpnelement rpnelements .
#rpnelements  -> "epsilon" .
#rpnelement   -> identifier .
#rpnelement   -> infixop .
#rpnelement   -> prefixop .
#rpnelement   -> fnkw .
#calling      -> "call" cbinding .
#cbinding     -> binding .
#cbinding     -> pkwbinding .
#application  -> "apply" abinding .
#abinding     -> binding .
#abinding     -> fkwbinding .
#typename     -> "typename" .
#fnkw         -> "fnkw" .
#scope        -> "scope" .
#prockw       -> "prockw" .
#prefixop     -> "prefixop" .
#infixop      -> "infixop" .
#identifier   -> "identifier" .
#literal      -> "literal" .

lex = lexer.lexer(sys.stdin)
nextsym()
program()