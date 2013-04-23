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
	elif sym[0] in varTypes:
		# don't eat type
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
	# FIRST: "identifier"
	# FOLLOW: "end-of-file", ";", "scope"
	procName = consume("ID", "identifier")[1]
	consume("LPAREN", "left parenthesis")
	formalparams()
	consume("RPAREN", "right parenthesis")
	consume("ASSIGN", "assignment")
	block()

def vardef(varScope, varType):
	# -> typename identifier "=" expression ";" . 
	# FIRST: "typename"
	# FOLLOW: "end-of-file", ";", "scope"
	varType = consume(varTypes, "variable type specifier")[0]
	varName = consume("ID", "identifier")[1]
	consume("ASSIGN", "assignment")
	expression()
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
	# -> definition      	FIRST: "scope"
	# -> kwstmt ";" 		FIRST: "while", "set", "rpn", "return", "cond", "call"
	# FIRST: "prebind", "prefixop", "set", "(", "identifier", "cond", 
	#        "call", "literal", "scope", "rpn", "return", "apply", "while"
	# FOLLOW: "prebind", "prefixop", "set", "apply", "(", "cond", "}", "while", 
	#         "literal", "scope", "rpn", "return", "identifier", "call"
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		expression()
		consume("SEMI", "semicolon")
	elif sym[0] in scopes:
		definition() # definitions include their own semicolon if needed
	elif sym[0] in ["WHILE", "SET", "RPN", "RETURN", "COND", "CALL"]:
		kwstmt()
		consume("SEMI", "semicolon")
	else: error("statement (expression; or definition; or keyword statement;)")

def expression():
	# -> term opterm .
	# FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	# check first set 
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		term()
		opterm()
	# let term() handle error case(s)

def term():
	# -> literal               FIRST: "literal"
	# -> prebinding .          FIRST: "prebind"
	# -> prefixop expression . FIRST: "prefixop"
	# -> indexable index .     FIRST: "apply", "identifier", "("
	# FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# FOLLOW: "infixop", "[", ")", ";", ","
	if sym[0] in literals:
		literal()
	elif sym[0] == "PREBIND":
		prebinding()
	elif sym[0] == "PREFIXOP":
		prefixop()
		expression()
	elif sym[0] in ["APPLY", "ID", "LPAREN"] :
		indexable()
		index()
	else: error("literal, prebinding, or indexable (prefix operator, function application, identifier, or left-paren)")

def opterm():
	# -> infixop expression opterm .
	# -> "epsilon"
	# FIRST: "infixop", "epsilon"
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	if sym[0] == "INFIXOP":
		operator = consume("INFIXOP", "infix operator")[1]
		#print "operator: " + operator
		expression()
		opterm()
	# epsilon: no "else"

def indexable():
	# -> identifier .         FIRST: "identifier"
	# -> application .        FIRST: "apply"
	# -> "(" expression ")" . FIRST: "("
	# FIRST: "apply", "identifier", "("
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	if sym[0] == "ID":
		identifier()
	elif sym[0] == "APPLY":
		application()
	elif consume("(", None):
		expression()
		consume(")", "right parenthesis")
	else: error("indexable (identifier, function application, or left-paren)")

def index():
	# -> "[" expression "]" .
	# -> "epsilon" .
	# FIRST: "epsilon", "["
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	if consume("LBRACKET", None):
		expression()
		consume("RBRACKET", "right square bracket")
	# epsilon: no "else"

def formalparams():
	# -> typename identifier moreformals .
	# -> "epsilon" .
	# FIRST: "epsilon", "typename"
	# FOLLOW: ")"
	if sym[0] in allTypes:
		paramType = consume(allTypes, None)[0]
		paramName = consume("ID", "identifier")[1]
		#print "formal param: ", paramType, paramName
		moreformals()
	# epsilon: no "else"

def moreformals():
	# -> "," formalparams .
	# -> "epsilon" .
	# FIRST: "epsilon", ","
	# FOLLOW: ")"
	if sym[0] == "COMMA":
		consume("COMMA", None)
		formalparams() 
	# epsilon: no "else"

def actualparams():
	# -> "@" identifier "=" expression moreactuals .  FIRST: "@"
	# -> expression moreactuals .                     FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# -> "epsilon" .                                  FIRST: "epsilon"
	# FIRST: "prebind", "prefixop", "(", "identifier", "@", "epsilon", "literal", "apply"
	# FOLLOW: 
	if consume("ATSIGN", None):
		identifier()
		consume("ASSIGN", "assignment")
		expression()
		moreactuals()
	elif sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		expression()
		moreactuals()
	# epsilon: no "else"

def moreactuals():
	# -> "," actualparams .
	# -> "epsilon" .
	# FIRST: "epsilon", ","
	# FOLLOW: ")"
	if consume("COMMA", None):
		actualparams()
	# epsilon: no "else"

def prebinding():
	# -> "prebind" binding .
	# FIRST: "prebind"
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	consume("PREBIND", "prebind")
	binding()

def binding():
	# -> identifier actuals . 
	# FIRST: "identifier"
	# FOLLOW: "]", "infixop", "[", ";", ")", ","
	name = consume("ID", "identifier")[1]
	actuals()

def fkwbinding():
	# -> fnkw actuals . 
	# FIRST: "fnkw"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	name = consume(funcKeys)[0]
	actuals()

def pkwbinding():
	# -> prockw actuals . 
	# FIRST: "prockw"
	# FOLLOW: ";"
	name = consume(procKeys)[0]
	actuals()

def actuals():
	# -> "(" actualparams ")" . 
	# FIRST: "("
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	consume("LPAREN", "left parenthesis")
	actualparams()
	consume("RPAREN", "right parenthesis")

def kwstmt():
	# -> "cond" "{" condelements "}" .        FIRST: "cond"
	# -> "while" "(" expression ")" block .   FIRST: "while"
	# -> "set" identifier "=" expression .    FIRST: "set"
	# -> "rpn" rpnelements .                  FIRST: "rpn"
	# -> "call" cbinding .                    FIRST: "call"
	# -> "return" expression .                FIRST: "return"
	# FIRST: "while", "set", "rpn", "return", "cond", "call"
	# FOLLOW: ";"
	if consume("COND", None):
		consume("LBRACE", "left curly brace")
		condelements()
		consume("RBRACE", "right curly brace")
	elif consume("WHILE", None):
		consume("LPAREN", "left parenthesis")
		expression()
		consume("RPAREN", "right parenthesis") 
		block()
	elif consume("SET", None):
		target = consume("ID", "identifier")[1]
		consume("ASSIGN", "assignment")
		expression()
	elif consume("RPN", None):
		rpnelements()
	elif consume("CALL", None):
		cbinding()
	elif consume("RETURN", None):
		expression()
	else: error("keyword (cond, while, set, rpn, call, return)")

def condelements():
	# -> "(" expression ")" block condelements .
	# -> "epsilon" .
	# FIRST: "epsilon", "("
	# FOLLOW: "}"
	if consume("LPAREN", None):
		expression()
		consume("RPAREN", "right parenthesis")
		block()
		condelements()
	# epsilon: no "else"

def rpnelements():
	# -> rpnelement rpnelements .
	# -> "epsilon" .
	# FIRST: "infixop", "prefixop", "fnkw", "identifier", "epsilon", "opkw", "literal"
	# FOLLOW: ";"
	if sym[0] in ["INFIXOP", "PREFIXOP", "ID"] + funcKeys + opKeys:
		rpnelement()
		rpnelements()
	# let rpnelement() handle error case(s)

def rpnelement():
	# -> identifier .
	# -> infixop .
	# -> prefixop .
	# -> fnkw .
	# -> opkw .
	# -> literal .
	# FIRST: "infixop", "prefixop", "fnkw", "identifier", "opkw", "literal"
	# FOLLOW: "infixop", "prefixop", "fnkw", "identifier", "opkw", "literal", ";"
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

def cbinding():
	# -> binding .
	# -> pkwbinding .
	# FIRST: "identifier", "prockw"
	# FOLLOW: ";"
	if sym[0] == "ID":
		binding()
	elif sym[0] in procKeys:
		pkwbinding()
	else: error("identifier or procedure keyword")

def application():
	# -> "apply" abinding
	# FIRST: "apply"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	consume("APPLY", "apply")
	abinding()

def abinding():
	# -> binding .
	# -> fkwbinding .
	# FIRST: "identifier", "fnkw"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	if sym[0] == "ID":
		binding()
	elif sym[0] in funcKeys:
		fkwbinding()
	else: error("identifier or function keyword")

def identifier():
	# -> "identifier"
	# FIRST: "identifier"
	# FOLLOW: "=", "prefixop", "(", ")", "infixop", "[", "]", ";", "fnkw", "identifier", "typename", ","
	name = consume("ID", "identifier")[1]
	#print "identifier: \"" + str(name) + "\""

def literal():
	# -> "literal"
	# FIRST: "literal"
	# FOLLOW: "infixop", "[", "_", "]", ";", ","
	type, value = consume(literals, "literal (int, real, string)")
	#print "literal of type " + type + " = " + str(value)


## Start It Up! ##

lex = lexer.lexer(sys.stdin)
nextsym()
program()
