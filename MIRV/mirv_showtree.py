#!/usr/bin/env python
import lexer, sys

EOF = "end-of-file"
sym = None


## Terminal Sets ##

varTypes = ["INT", "REAL", "ARRAY", "LIST", "STRING", "MATRIX"]
allTypes = varTypes + ["PROC", "FUNC"]
scopes   = ["DEF", "GLOBAL", "LET", "LOCAL"]
literals = ["INT", "REAL", "STRING"]#, "CHAR", "ARRAY", "MATRIX", "BOOL"]
funcKeys = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sqrt', 'peek', 'pop', 'store']
procKeys = ['_error_', '_init_', '_loop_', 'push', 'load']
opKeys   = ['and', 'or', 'not']
valKeys  = ['true', 'false', 'empty', 'invalid',]


## Streamy Stuff ##

def nextsym():
	global sym
	try:
		sym = lex.next()
	except StopIteration as i:
		sym = (EOF, None)
	#print sym

def error(expected):
	print "ERROR: expected " + expected + ", got " + sym[0]
	sys.exit("bailing -- no panic mode yet")

def consume(target, english): # "None" for english when missing symbol is ok
	if (isinstance(target, list) and sym[0] in target) \
	    or sym[0] == target:
		ret = sym
		nextsym()
		return ret
	elif english: error(english)
	else: return None


### Recursors ###

def program(depth):
	# -> definitions .
	# FIRST: "scope"
	# FOLLOW: "end-of-file"
	print "| "*depth + "program"
	definitions(depth+1)

def definitions(depth):
	# -> definition definitions .
	# -> "epsilon" .
	# FIRST: "epsilon", "scope"
	# FOLLOW: "end-of-file"
	print "| "*depth + "definitions"
	if sym[0] != EOF:
		definition(depth+1)
		definitions(depth+1)

def definition(depth):
	# -> scope deftype .
	# FIRST: "scope"
	# FOLLOW: "end-of-file", ";", "scope"
	print "| "*depth + "definition"
	scope = consume(scopes, "scope symbol")[0]
	deftype(depth+1, scope)

def deftype(depth, defScope):
	# -> "func" funcdef .
	# -> "proc" procdef .
	# -> typename vardef .
	# FIRST: "func", "typename", "proc"
	# FOLLOW: "end-of-file", ";", "scope"
	print "| "*depth + "deftype"
	if sym[0] == "FUNC":
		nextsym()
		funcdef(depth+1, defScope)
	elif sym[0] == "PROC":
		nextsym()
		procdef(depth+1, defScope)
	elif sym[0] in varTypes:
		# don't eat type
		vardef(depth+1, defScope, sym[1])
	else: error("type specifier")

def funcdef(depth, funcScope):
	# -> typename identifier "(" formalparams ")"  "=" block .
	# FIRST: "typename"
	# FOLLOW: "end-of-file", ";", "scope"
	print "| "*depth + "funcdef"
	funcReturnType = consume(varTypes, "variable type specifier")[0] # FUNC/PROC handled separately
	funcName = consume("ID", "identifier")[1]
	print "| " * depth + "function setup: ", funcScope, funcReturnType, funcName
	consume("LPAREN", "left parenthesis")
	formalparams(depth+1)
	consume("RPAREN", "right parenthesis")
	consume("ASSIGN", "assignment")
	block(depth+1)

def procdef(depth, procScope):
	# -> identifier "(" formalparams ")"  "=" block .
	# FIRST: "identifier"
	# FOLLOW: "end-of-file", ";", "scope"
	print "| "*depth + "procdef"
	procName = consume("ID", "identifier")[1]
	consume("LPAREN", "left parenthesis")
	formalparams(depth+1)
	consume("RPAREN", "right parenthesis")
	consume("ASSIGN", "assignment")
	block(depth+1)

def vardef(depth, varScope, varType):
	# -> typename identifier "=" expression ";" . 
	# FIRST: "typename"
	# FOLLOW: "end-of-file", ";", "scope"
	print "| "*depth + "vardef"
	varType = consume(varTypes, "variable type specifier")[0]
	varName = consume("ID", "identifier")[1]
	consume("ASSIGN", "assignment")
	expression(depth+1)
	consume("SEMI", "semicolon")
	
def block(depth):
	# -> "{" statements "}" . 
	# FIRST: "{"
	# FOLLOW: "}", "end-of-file", ";", "scope", "("
	print "| "*depth + "block"
	consume("LBRACE", "left curly brace")
	statements(depth+1)
	consume("RBRACE", "right curly brace")

def statements(depth):
	# -> statement statements .
	# -> "epsilon" .
	# FIRST: "prebind", "prefixop", "set", "(", "identifier", "cond", "epsilon", 
	#        "call", "literal", "scope", "rpn", "return", "apply", "while"
	# FOLLOW: "}"
	print "| "*depth + "statements"
	if sym[0] in ["PREBIND", "PREFIXOP", "SET", "LPAREN", "ID", "COND", "CALL", "RPN", \
				  "RETURN", "APPLY", "WHILE"] + literals + scopes:
		# don't eat symbol; we don't use it here
		statement(depth+1)
		statements(depth+1)
	# epsilon: no "else"

def statement(depth):
	# -> expression ";" 	FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# -> definition      	FIRST: "scope"
	# -> kwstmt ";" 		FIRST: "while", "set", "rpn", "return", "cond", "call"
	# FIRST: "prebind", "prefixop", "set", "(", "identifier", "cond", 
	#        "call", "literal", "scope", "rpn", "return", "apply", "while"
	# FOLLOW: "prebind", "prefixop", "set", "apply", "(", "cond", "}", "while", 
	#         "literal", "scope", "rpn", "return", "identifier", "call"
	print "| "*depth + "statement"
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		expression(depth+1)
		consume("SEMI", "semicolon")
	elif sym[0] in scopes:
		definition(depth+1) # definitions include their own semicolon if needed
	elif sym[0] in ["WHILE", "SET", "RPN", "RETURN", "COND", "CALL"]:
		kwstmt(depth+1)
		consume("SEMI", "semicolon")
	else: error("statement (expression; or definition; or keyword statement;)")

def expression(depth):
	# -> term opterm .
	# FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	# check first set 
	print "| "*depth + "expression"
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		term(depth+1)
		opterm(depth+1)
	# let term() handle error case(s)

def term(depth):
	# -> literal               FIRST: "literal"
	# -> prebinding .          FIRST: "prebind"
	# -> prefixop expression . FIRST: "prefixop"
	# -> indexable index .     FIRST: "apply", "identifier", "("
	# FIRST: "prebind", "literal", "apply", "identifier", "("
	# FOLLOW: "infixop", "[", ")", ";", ","
	print "| "*depth + "term"
	if sym[0] in literals:
		literal(depth+1)
	elif sym[0] == "PREBIND":
		prebinding(depth+1)
	elif sym[0] == "PREFIXOP":
		prefixop(depth+1)
		expression(depth+1)
	elif sym[0] in ["APPLY", "ID", "LPAREN"] :
		indexable(depth+1)
		index(depth+1)
	else: error("literal, prebinding, or indexable (prefix operator, function application, identifier, or left-paren)")

def opterm(depth):
	# -> infixop expression opterm .
	# -> "epsilon"
	# FIRST: "infixop", "epsilon"
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	print "| "*depth + "opterm"
	if sym[0] == "INFIXOP":
		operator = consume("INFIXOP", "infix operator")[1]
		print "| "*depth +  "operator: " + operator
		expression(depth+1)
	 	opterm(depth+1)
	# epsilon: no "else"

def indexable(depth):
	# -> identifier .          FIRST: "identifier"
	# -> application .         FIRST: "apply"
	# -> "(" expression ")" .  FIRST: "("
	# FIRST: "apply", "identifier", "prefixop", "("
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	print "| "*depth + "indexable"
	if sym[0] == "ID":
		identifier(depth+1)
	elif sym[0] == "APPLY":
		application(depth+1)
	elif consume("(", None):
		expression(depth+1)
		consume(")", "right parenthesis")
	else: error("indexable (identifier, function application, or left-paren)")

def index(depth):
	# -> "[" expression "]" .
	# -> "epsilon" .
	# FIRST: "epsilon", "["
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	print "| "*depth + "index"
	if consume("LBRACKET", None):
		expression(depth+1)
		consume("RBRACKET", "right square bracket")
	# epsilon: no "else"

def formalparams(depth):
	# -> typename identifier moreformals .
	# -> "epsilon" .
	# FIRST: "epsilon", "typename"
	# FOLLOW: ")"
	print "| "*depth + "formalparams"
	if sym[0] in allTypes:
		paramType = consume(allTypes, None)[0]
		paramName = consume("ID", "identifier")[1]
		print "| "*depth + "formal param: ", paramType, paramName
		moreformals(depth+1)
	# epsilon: no "else"

def moreformals(depth):
	# -> "," formalparams .
	# -> "epsilon" .
	# FIRST: "epsilon", ","
	# FOLLOW: ")"
	print "| "*depth + "moreformals"
	if sym[0] == "COMMA":
		consume("COMMA", None)
		formalparams(depth+1) 
	# epsilon: no "else"

def actualparams(depth):
	# -> "@" identifier "=" expression moreactuals .  FIRST: "@"
	# -> expression moreactuals .                     FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# -> "epsilon" .                                  FIRST: "epsilon"
	# FIRST: "prebind", "prefixop", "(", "identifier", "@", "epsilon", "literal", "apply"
	# FOLLOW: 
	print "| "*depth + "actualparams"
	if consume("ATSIGN", None):
		identifier(depth+1)
		consume("ASSIGN", "assignment")
		expression(depth+1)
		moreactuals(depth+1)
	elif sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		expression(depth+1)
		moreactuals(depth+1)
	# epsilon: no "else"

def moreactuals(depth):
	# -> "," actualparams .
	# -> "epsilon" .
	# FIRST: "epsilon", ","
	# FOLLOW: ")"
	print "| "*depth + "moreactuals"
	if consume("COMMA", None):
		actualparams(depth+1)
	# epsilon: no "else"

def prebinding(depth):
	# -> "prebind" binding .
	# FIRST: "prebind"
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	print "| "*depth + "prebinding"
	consume("PREBIND", "prebind")
	binding(depth+1)

def binding(depth):
	# -> identifier actuals . 
	# FIRST: "identifier"
	# FOLLOW: "]", "infixop", "[", ";", ")", ","
	print "| "*depth + "binding"
	name = consume("ID", "identifier")[1]
	actuals(depth+1)

def fkwbinding(depth):
	# -> fnkw actuals . 
	# FIRST: "fnkw"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	print "| "*depth + "fkwbinding"
	name = consume(funcKeys)[0]
	actuals(depth+1)

def pkwbinding(depth):
	# -> prockw actuals . 
	# FIRST: "prockw"
	# FOLLOW: ";"
	print "| "*depth + "pkwbinding"
	name = consume(procKeys)[0]
	actuals(depth+1)

def actuals(depth):
	# -> "(" actualparams ")" . 
	# FIRST: "("
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	print "| "*depth + "actuals"
	consume("LPAREN", "left parenthesis")
	actualparams(depth+1)
	consume("RPAREN", "right parenthesis")

def kwstmt(depth):
	# -> "cond" "{" condelements "}" .        FIRST: "cond"
	# -> "while" "(" expression ")" block .   FIRST: "while"
	# -> "set" identifier "=" expression .    FIRST: "set"
	# -> "rpn" rpnelements .                  FIRST: "rpn"
	# -> "call" cbinding .                    FIRST: "call"
	# -> "return" expression .                FIRST: "return"
	# FIRST: "while", "set", "rpn", "return", "cond", "call"
	# FOLLOW: ";"
	print "| "*depth + "kwstmt"
	if consume("COND", None):
		consume("LBRACE", "left curly brace")
		condelements(depth+1)
		consume("RBRACE", "right curly brace")
	elif consume("WHILE", None):
		consume("LPAREN", "left parenthesis")
		expression(depth+1)
		consume("RPAREN", "right parenthesis") 
		blockdepth+1()
	elif consume("SET", None):
		target = consume("ID", "identifier")[1]
		consume("ASSIGN", "assignment")
		expression(depth+1)
	elif consume("RPN", None):
		rpnelements(depth+1)
	elif consume("CALL", None):
		cbinding(depth+1)
	elif consume("RETURN", None):
		expression(depth+1)
	else: error("keyword (cond, while, set, rpn, call, return)")

def condelements(depth):
	# -> "(" expression ")" block condelements .
	# -> "epsilon" .
	# FIRST: "epsilon", "("
	# FOLLOW: "}"
	print "| "*depth + "condelements"
	if consume("LPAREN", None):
		expression(depth+1)
		consume("RPAREN", "right parenthesis")
		block(depth+1)
		condelements(depth+1)
	# epsilon: no "else"

def rpnelements(depth):
	# -> rpnelement rpnelements .
	# -> "epsilon" .
	# FIRST: "infixop", "prefixop", "fnkw", "identifier", "epsilon", "opkw", "literal"
	# FOLLOW: ";"
	print "| "*depth + "rpnelements"
	if sym[0] in ["INFIXOP", "PREFIXOP", "ID"] + funcKeys + opKeys:
		rpnelement(depth+1)
		rpnelements(depth+1)
	# let rpnelement() handle error case(s)

def rpnelement(depth):
	# -> identifier .
	# -> infixop .
	# -> prefixop .
	# -> fnkw .
	# -> opkw .
	# -> literal .
	# FIRST: "infixop", "prefixop", "fnkw", "identifier", "opkw", "literal"
	# FOLLOW: "infixop", "prefixop", "fnkw", "identifier", "opkw", "literal", ";"
	print "| "*depth + "rpnelement"
	if sym[0] == "ID":
		name = consume("ID", None)[1]
	elif sym[0] == "INFIXOP":
		operator = consume("INFIXOP", None)[1]
	elif sym[0] == "PREFIXOP":
		operator = consume("PREFIXOP", None)[1]
	elif sym[0] in funcKeys:
		function = consume(funcKeys, None)[0]
	elif sym[0] in opKeys:
		operator = consume(opKeys, None)[0]
	elif sym[0] in literals:
		type, value = consume(literals, None)
	else: error("operator, function, variable, or literal value")

def cbinding(depth):
	# -> binding .
	# -> pkwbinding .
	# FIRST: "identifier", "prockw"
	# FOLLOW: ";"
	print "| "*depth + "cbinding"
	if sym[0] == "ID":
		binding(depth+1)
	elif sym[0] in procKeys:
		pkwbinding(depth+1)
	else: error("identifier or procedure keyword")

def application(depth):
	# -> "apply" abinding
	# FIRST: "apply"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	print "| "*depth + "application"
	consume("APPLY", "apply")
	abinding(depth+1)

def abinding(depth):
	# -> binding .
	# -> fkwbinding .
	# FIRST: "identifier", "fnkw"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	print "| "*depth + "abinding"
	if sym[0] == "ID":
		binding(depth+1)
	elif sym[0] in funcKeys:
		fkwbinding(depth+1)
	else: error("identifier or function keyword")

def identifier(depth):
	# -> "identifier"
	# FIRST: "identifier"
	# FOLLOW: "=", "prefixop", "(", ")", "infixop", "[", "]", ";", "fnkw", "identifier", "typename", ","
	print "| "*depth + "identifier"
	name = consume("ID", "identifier")[1]
	print "| "*depth + "identifier: \"" + str(name) + "\""

def literal(depth):
	# -> "literal"
	# FIRST: "literal"
	# FOLLOW: "infixop", "[", "_", "]", ";", ","
	print "| "*depth + "literal"
	type, value = consume(literals, "literal (int, real, string)")
	print "| "*depth + "literal of type " + type + " = " + str(value)


## Start It Up! ##

lex = lexer.lexer(sys.stdin)
nextsym()
program(0)
