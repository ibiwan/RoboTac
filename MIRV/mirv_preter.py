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

# FIRST: "scope"
# FOLLOW: "end-of-file"
def program():
	root = node_classes.Program() # AST
	# -> { definition } .
	while sym[0] != EOF:
		definition(root, root)

# FIRST: "scope"
# FOLLOW: = FOLLOW(statement) + 'end-of-file'
def definition(rootScope, currScope):
	# -> scope ( funcDef | procDef | varDef ) .
	defScope = consume(scopes, "scope")[0]
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

# FIRST: "func"
# FOLLOW: = FOLLOW(statement) + 'end-of-file'
def funcdef(rootScope, funcScope):
	# -> "func" typename identifier formalparams "(" "=" ")" block .
	consume("FUNC", "func")
	funcReturnType = consume(varTypes, "variable type specifier")[0] # FUNC/PROC handled separately
	funcName = consume("ID", "identifier")[1]
	#print "function setup: ", funcScope, funcReturnType, funcName
	consume("LPAREN", "open paren")
	formalparams()
	consume("RPAREN", "close paren")
	consume("ASSIGN", "assignment")
	block(rootScope, funcScope)

# FIRST: "proc"
# FOLLOW: = FOLLOW(statement) + 'end-of-file'
def procdef(rootScope, procScope):
	# -> "proc" identifier "(" formalparams ")" =" block .
	consume("PROC", "proc")
	procName = consume("ID", "identifier")[1]
	consume("LPAREN", "open paren")
	formalparams()
	consume("RPAREN", "close paren")
	consume("ASSIGN", "assignment")
	block(rootScope, procScope)

# FIRST: "typename"
# FOLLOW: = FOLLOW(statement) + 'end-of-file'
def vardef(rootScope, varScope, varType):
	# -> typename identifier "=" expression ";" . 
	varType = consume(varTypes, "variable type specifier")[0]
	varName = consume("ID", "identifier")[1]
	consume("ASSIGN", "assignment")
	expression()
	consume("SEMI", "semicolon")
	
# FIRST: "{"
# FOLLOW: = FOLLOW(statement) + 'end-of-file'
def block(rootScope, currScope):
	# -> "{" { statement } "}" . 
	consume("LBRACE", "open brace")
	while sym[0] in ["PREBIND", "PREFIXOP", "SET", "LPAREN", "ID", "COND", "CALL", "RPN", \
				  "RETURN", "APPLY", "WHILE"] + literals + scopes:
		statement(rootScope, currScope)
	consume("RBRACE", "close brace")

# FIRST: '(', 'apply', 'call', 'cond', 'identifier', 'literal', 'prebind', 
#        'prefixop', 'return', 'rpn', 'scope', 'set', 'tcall', 'while''
# FOLLOW: = FIRST(statement) + '}'
def statement(rootScope, currScope):
	# -> definition                            FIRST: "scope"
	if sym[0] in scopes:
		definition(rootScope, currScope) 
		# ends with block, not semicolon
	# -> "while" while_s .                     FIRST: "while"
	elif sym[0] == "WHILE":
		while_s()
		# ends with block, not semicolon
	# -> "cond" cond .                         FIRST: "cond"
	elif sym[0] == "COND":
		cond(rootScope, currScope)
		# ends with block, not semicolon
	# -> expression ";" .                      FIRST: "prebind", "prefixop", "literal", "apply", "identifier", "("
	elif sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN"] + literals:
		expression()
		consume("SEMI", "semicolon")
	# -> ( "call" | "tcall" ) cbinding ";" .   FIRST: "call", "tcall"
	elif sym[0] in ["CALL", "TCALL"]:
		call()
		consume("SEMI", "semicolon")
	# -> "set" identifier "=" expression ";" . FIRST: "set"
	elif consume("SET", None):
		target = consume("ID", "identifier")[1]
		consume("ASSIGN", "assignment")
		expression()
		consume("SEMI", "semicolon")
	# -> "rpn" rpnelements ";" .               FIRST: "rpn"
	elif consume("RPN", None):
		while sym[0] in ["INFIXOP", "PREFIXOP", "ID"] + funcKeys + opKeys:
			rpnelement()
		consume("SEMI", "semicolon")
	# -> "return" expression ";" .             FIRST: "return"
	elif consume("RETURN", None):
		expression()
		consume("SEMI", "semicolon")
	else: error("statement (while, expression, definition, or keyword statement)")

# FIRST: = FIRST(term)
# FOLLOW: = FOLLOW(term)
def expression():
	# -> term { "infixop" expression } .
	term()
	while sym[0] == "INFIXOP":
		operator = consume("INFIXOP", "infix operator")[1]
		#print "operator: " + operator
		expression()

# FIRST: '(', 'apply', 'identifier', 'literal', 'prebind', 'prefixop'
# FOLLOW: ')', ',', ';', '[', ']', 'infixop'
def term():
	# -> literal               FIRST: "literal"
	if sym[0] in literals: # array literals not supported: never indexable
		type, value = consume(literals, "literal (int, real, string)")
	# -> prebinding .          FIRST: "prebind"
	elif sym[0] == "PREBIND": # prebind only returns subroutines: never indexable
		binding()
	# -> indexable index .     FIRST: "prefixop", "apply", "identifier", "("
	elif sym[0] in ["PREFIXOP", "APPLY", "ID", "LPAREN"] :
		indexable()
		if consume("LBRACKET", None):
			expression()
			consume("RBRACKET", "close bracket")
	else: error("literal, prebinding, or indexable (prefix operator, function application, identifier, or left-paren)")

# FIRST: '(', 'apply', 'identifier', 'prefixop'
# FOLLOW: = FOLLOW(term)
def indexable():
	# -> identifier .         FIRST: "identifier"
	if sym[0] == "ID": # identifier could refer to an array
		name = consume("ID", "identifier")[1]
	# -> application .        FIRST: "apply"
	elif sym[0] == "APPLY": # function could return an array
		application()
	# -> prefixop expression . FIRST: "prefixop"
	elif sym[0] == "PREFIXOP": # could "pop x" to retrieve an array from the stack
		operator = consume("PREFIXOP", "prefix operator")[1]
		expression()
	# -> "(" expression ")" . FIRST: "("
	elif consume("(", None): # expression could evaluate to an array
		expression()
		consume(")", "close paren")
	else: error("indexable (identifier, function application, or left-paren)")

# FIRST: 'epsilon', 'typename'
# FOLLOW: ')'
def formalparams(mandatory = False):
	# -> [ "typename" identifier [ "," formalparams ] ] .
	if sym[0] in allTypes:
		paramType = consume(allTypes, None)[0]
		paramName = consume("ID", "identifier")[1]
		if consume("COMMA", None):
			formalparams(True)
	elif mandatory: # no trailing commas
		error("typename")

# FIRST: = FIRST(term) + '@' + 'epsilon'
# FOLLOW: ')'
def actualparams(mandatory = False):
	# -> [ [ "@" identifier "=" ] expression [ "," actualparams ] ] .
	if sym[0] in ["PREBIND", "PREFIXOP", "APPLY", "ID", "LPAREN", "ATSIGN"] + literals:
		if consume("ATSIGN", None):
			name = consume("ID", "identifier")[1]
			consume("ASSIGN", "assignment")
		expression()
		if consume("COMMA", None):
			actualparams(True)
	elif mandatory: # no trailing commas
		error("prebind, prefixop, application, identifier, left paren, binding (@), or literal")

# FIRST: 'prebind'
# FOLLOW: = FOLLOW(term)
def prebinding():
	# -> "prebind" identifier "(" actualparams ")" . 
	consume("PREBIND", "prebind")
	name = consume("ID", "identifier")[1]
	consume("LPAREN", "open paren")
	actualparams()
	consume("RPAREN", "close paren")

# FIRST: 'cond'
# FOLLOW: = FOLLOW(statement)
def cond(rootScope, currScope):
	# -> "cond" "{" { ( expression ) block } "}" .        
	consume("COND", "cond")
	consume("LBRACE", "open brace")
	while consume("LPAREN", None):
		expression()
		consume("RPAREN", "close paren")
		block(rootScope, currScope)
	consume("RBRACE", "close brace")

# FIRST: 'while'
# FOLLOW: = FOLLOW(statement)
def while_s(rootScope, curreScope):
	# -> "while" "(" expression ")" block
	consume("LPAREN", "open paren")
	expression()
	consume("RPAREN", "close paren") 
	block(rootScope, currScope)

# FIRST: 'fnkw', 'identifier', 'infixop', 'literal', 'opkw', 'prefixop'
# FOLLOW: = FIRST(rpnelement) + ';'
def rpnelement():
	# -> identifier .
	if sym[0] == "ID":
		name = consume("ID", None)[1]
	# -> infixop .
	elif sym[0] == "INFIXOP":
		operator = consume("INFIXOP", None)[1]
	# -> prefixop .
	elif sym[0] == "PREFIXOP":
		operator = consume("PREFIXOP", None)[1]
	# -> fnkw .
	elif sym[0] in funcKeys:
		function = consume(funcKeys, None)[0]
	# -> opkw .
	elif sym[0] in opKeys:
		operator = consume(opKeys, None)[0]
	# -> literal .
	elif sym[0] in literals:
		type, value = consume(literals, None)
	else: error("operator, function, variable, or literal value")

# FIRST: 'call', 'tcall'
# FOLLOW: = FOLLOW(statement)
def call():
	# -> ( "call" | "tcall" ) ( identifier | prockw )  "(" actualparams ")" .
	consume(["CALL", "TCALL"], "call or tail-call")
	if sym[0] == "ID":
		name = consume("ID", "identifier")[1]
	elif sym[0] in procKeys:
		name = consume(procKeys)[0]
	else: error("identifier or procedure keyword")
	consume("LPAREN", "open paren")
	actualparams()
	consume("RPAREN", "close paren")

# FIRST: 'apply'
# FOLLOW: = FOLLOW(term)
def application():
	# -> "apply" ( fnkw | identifier )  "(" actualparams ")" .
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
