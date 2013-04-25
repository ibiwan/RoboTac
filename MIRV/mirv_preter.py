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
kwStmts  = ["SET", "RPN", "RETURN", "COND", "CALL", "TCALL"]

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
	    or sym[0] == target: # relying on short-circuited "or"
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
		definition(root, root)

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
	# -> "func" typename identifier formalparams "(" "=" ")" block .
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
	# -> "proc" identifier "(" formalparams ")" =" block .
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
	# -> "while" while_s .  FIRST: "while"
	# -> kwstmt ";" 		FIRST: "set", "rpn", "return", "cond", "call"
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
	elif sym[0] == "WHILE":
		while_s()
	elif sym[0] in kwStmts:
		kwstmt(rootScope, currScope)
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
		binding()
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
		name = consume("ID", "identifier")[1]
	elif sym[0] == "APPLY":
		application()
	elif consume("(", None):
		expression()
		consume(")", "close paren")
	else: error("indexable (identifier, function application, or left-paren)")

def formalparams():
	# -> [ "typename" identifier [ "," formalparams ] ] .
	# FIRST: "typename"
	# FOLLOW: 
	if paramType = consume(allTypes, None)[0]:
		paramName = consume("ID", "identifier")[1]
		if consume("COMMA", None):
			formalparams()

def actualparams():
	# -> [ [ "@" identifier "=" ] expression [ "," actualparams ] ] .
	# FIRST: "@", "prebind", "prefixop", "apply", "identifier", "(", "literal"
	# FOLLOW: 
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN", "ATSIGN"] + literals:
		if consume("ATSIGN", None):
			name = consume("ID", "identifier")[1]
			consume("ASSIGN", "assignment")
		expression()
		if consume("COMMA", None):
			actualparams()

def prebinding():
	# -> "prebind" identifier "(" actualparams ")" . 
	# FIRST: "identifier"
	# FOLLOW: "]", "infixop", "[", ";", ")", ","
	consume("PREBIND", "prebind")
	name = consume("ID", "identifier")[1]
	consume("LPAREN", "open paren")
	actualparams()
	consume("RPAREN", "close paren")

def kwstmt(rootScope, currScope):
	# -> "cond" cond .        FIRST: "cond"
	# -> "set" identifier "=" expression .    FIRST: "set"
	# -> "rpn" rpnelements .                  FIRST: "rpn"
	# -> "call" cbinding .                    FIRST: "call"
	# -> "return" expression .                FIRST: "return"
	# FIRST: "set", "rpn", "return", "cond", "call"
	# FOLLOW: ";"
	if sym[0] == "COND":
		cond(rootScope, currScope)
	elif consume("SET", None):
		target = consume("ID", "identifier")[1]
		consume("ASSIGN", "assignment")
		expression()
	elif consume("RPN", None):
		while sym[0] in ["INFIXOP", "PREFIXOP", "ID"] + funcKeys + opKeys:
			rpnelement()
	elif sym[0] in ["CALL", "TCALL"]:
		call()
	elif consume("RETURN", None):
		expression()
	else: error("keyword (cond, while, set, rpn, call, return)")

def cond(rootScope, currScope):
	# -> "cond" "{" condelements "}" .        FIRST: "cond"
	# FIRST: "cond"
	# FOLLOW: ";"
	consume("COND", "cond"):
	consume("LBRACE", "open brace")
	while consume("LPAREN", None):
		expression()
		consume("RPAREN", "close paren")
		block(rootScope, currScope)
	consume("RBRACE", "close brace")

def while_s(rootScope, curreScope):
	# -> "while" "(" expression ")" block
	# FIRST: "while"
	# FOLLOW: 
	consume("LPAREN", "open paren")
	expression()
	consume("RPAREN", "close paren") 
	block(rootScope, currScope)

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

def call():
	# -> ( "call" | "tcall" ) ( identifier | prockw )  "(" actualparams ")" .
	# -> "prockw" actualparams .
	# FIRST: "identifier", "prockw"
	# FOLLOW: ";"
	consume(["CALL", "TCALL"], "call or tail-call")
	if sym[0] == "ID":
		name = consume("ID", "identifier")[1]
	elif sym[0] in procKeys:
		name = consume(procKeys)[0]
	else: error("identifier or procedure keyword")
	consume("LPAREN", "open paren")
	actualparams()
	consume("RPAREN", "close paren")

def application():
	# -> "apply" ( fnkw | identifier )  "(" actualparams ")" .
	# FIRST: "apply"
	# FOLLOW: "]", "infixop", ";", "[", ")", ","
	consume("APPLY", "apply")
	if sym[0] == "ID":
		name = consume("ID", "identifier")[1]
	elif sym[0] in funcKeys:
		name = consume(funcKeys)[0]
	else: error("identifier or function keyword")
	consume("LPAREN", "open paren")
	actualparams()
	consume("RPAREN", "close paren")


## Start It Up! ##

lex = lexer.lexer(sys.stdin) # create token generator
nextsym() # initialize sym
program() # start parsing at the start symbol
