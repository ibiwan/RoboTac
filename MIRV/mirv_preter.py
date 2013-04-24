#!/usr/bin/env python
import lexer, sys
import node_classes

EOF = "end-of-file"
sym = None


## Terminal Sets ##

varTypes = ["INT", "REAL", "ARRAY", "LIST", "STRING", "MATRIX"]
allTypes = varTypes + ["PROC", "FUNC"]
locals   = ["LET", "LOCAL"]
globals  = ["DEF", "GLOBAL"]
scopes   = locals + globals
literals = ["INT", "REAL", "STRING"]#, "CHAR", "ARRAY", "MATRIX", "BOOL"]
funcKeys = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sqrt', 'peek', 'pop', 'store']
procKeys = ['_error_', '_init_', '_loop_', 'push', 'load']
opKeys   = ['and', 'or', 'not']
valKeys  = ['true', 'false', 'empty', 'invalid',]
kwStmts  = ["WHILE", "SET", "RPN", "RETURN", "COND", "CALL"]

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
	# -> { definition } .
	# FIRST: "scope"
	# FOLLOW: "end-of-file"
	while sym[0] != EOF:
		root = node_classes.Program() # AST
		definitions(root, root)

def definition(rootScope, currScope):
	# -> scope ( funcDef | procDef | varDef ) .
	# FIRST: "scope"
	# FOLLOW: "end-of-file", ";", "scope"
	defScope = consume(scopes, "scope symbol")[0]
	useScope = currScope if defScope in locals else rootScope
	if defScope in locals: print "should be local"
	print useScope
	if sym[0] == "FUNC":
		funcdef(rootScope, defScope)
	elif sym[0] == "PROC":
		procdef(rootScope, defScope)
	elif sym[0] in varTypes:
		vardef(rootScope, defScope, sym[1])
	else: error("type specifier")

def funcdef(rootScope, funcScope):
	# -> "func" typename identifier "(" formalparams ")"  "=" block .
	# FIRST: "func"
	# FOLLOW: "end-of-file", ";", "scope"
	consume("FUNC", "func")
	funcReturnType = consume(varTypes, "variable type specifier")[0] # FUNC/PROC handled separately
	funcName = consume("ID", "identifier")[1]
	#print "function setup: ", funcScope, funcReturnType, funcName
	consume("LPAREN", "open paren")
	formalparams()
	consume("RPAREN", "close paren")
	consume("ASSIGN", "assignment")
	block(rootScope, funcScope)


def procdef(rootScope, procScope):
	# -> "proc" identifier "(" formalparams ")"  "=" block .
	# FIRST: "proc"
	# FOLLOW: "end-of-file", ";", "scope"
	consume("PROC", "proc")
	procName = consume("ID", "identifier")[1]
	consume("LPAREN", "open paren")
	formalparams()
	consume("RPAREN", "close paren")
	consume("ASSIGN", "assignment")
	block(rootScope, procScope)

def vardef(rootScope, varScope, varType):
	# -> typename identifier "=" expression ";" . 
	# FIRST: "typename"
	# FOLLOW: "end-of-file", ";", "scope"
	varType = consume(varTypes, "variable type specifier")[0]
	varName = consume("ID", "identifier")[1]
	consume("ASSIGN", "assignment")
	expression()
	consume("SEMI", "semicolon")
	
def block(rootScope, currScope):
	# -> "{" { statement } "}" . 
	# FIRST: "{"
	# FOLLOW: "}", "end-of-file", ";", "scope", "("
	consume("LBRACE", "open brace")
	while sym[0] in ["PREBIND", "PREFIXOP", "SET", "LPAREN", "ID", "COND", "CALL", "RPN", \
				  "RETURN", "APPLY", "WHILE"] + literals + scopes:
		statement(rootScope, currScope)
	consume("RBRACE", "close brace")

def statement(rootScope, currScope):
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
		definition(rootScope, currScope) 
		# definitions include their own semicolon if needed
	elif sym[0] in kwStmts:
		kwstmt()
		consume("SEMI", "semicolon")
	else: error("statement (expression, definition, or keyword statement)")

def expression():
	# -> term opterm .
	# FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# FOLLOW: "infixop", "[", ")", "]", ";", ","
	# check first set 
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		term()
		while sym[0] == "INFIXOP":
			operator = consume("INFIXOP", "infix operator")[1]
			#print "operator: " + operator
			expression()

def term():
	# -> literal               FIRST: "literal"
	# -> prebinding .          FIRST: "prebind"
	# -> prefixop expression . FIRST: "prefixop"
	# -> indexable index .     FIRST: "apply", "identifier", "("
	# FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	# FOLLOW: "infixop", "[", ")", ";", ","
	if sym[0] in literals:
		type, value = consume(literals, "literal (int, real, string)")
	elif sym[0] == "PREBIND":
		prebinding()
	elif sym[0] == "PREFIXOP":
		operator = consume("PREFIXOP", "prefix operator")[1]
		expression()
	elif sym[0] in ["APPLY", "ID", "LPAREN"] :
		indexable()
		if consume("LBRACKET", None):
			expression()
			consume("RBRACKET", "close bracket")
	else: error("literal, prebinding, or indexable (prefix operator, function application, identifier, or left-paren)")

def indexable():
	# -> identifier .         FIRST: "identifier"
	# -> application .        FIRST: "apply"
	# -> "(" expression ")" . FIRST: "("
	# FIRST: "apply", "identifier", "("
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	if sym[0] == "ID":
		name = consume("ID", "identifier")[1])
	elif sym[0] == "APPLY":
		application()
	elif consume("(", None):
		expression()
		consume(")", "close paren")
	else: error("indexable (identifier, function application, or left-paren)")

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
		name = consume("ID", "identifier")[1]
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
	consume("LPAREN", "open paren")
	actualparams()
	consume("RPAREN", "close paren")

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
		consume("LBRACE", "open brace")
		condelements()
		consume("RBRACE", "close brace")
	elif consume("WHILE", None):
		consume("LPAREN", "open paren")
		expression()
		consume("RPAREN", "close paren") 
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
		consume("RPAREN", "close paren")
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


## Start It Up! ##

lex = lexer.lexer(sys.stdin)
nextsym()
program()
