#!/usr/bin/env python
import sys

class Type:
	INT, REAL, STRING, ARRAY = range(4)

class Operator:
	PLUS, MINUS, TIMES, DIVIDE = range(4)

class Scope:
	def __init__(self, parent):
		self.definitions = dict()
		self.parent = parent # Scope
	def add(self, name, definition):
		print "adding to scope"
		if self.definitions.has_key(name):
			print "attempting to re-define name \"" + name + "\""
			sys.exit("re-defining?  I'm outta here")
		self.definitions[name] = definition
	def has_key(self, key):
		return self.definitions.has_key(key)
	def __getitem__(self, item):
		return self.definitions[item]
	def __str__(self):
		ret = "Scope: "
		ret += str(len(self.definitions)) + " items defined:\n"
		for defn in self.definitions:
			ret += str(defn) + " is a...\n" + str(self.definitions[defn])
		return ret

class Block:
	def __init__(self):
		self.statements = []
	def add(self, statement):
		self.statements.append(statement)
	def __str__(self):
		ret = "Block:\n"
		for stmt in self.statements:
			ret += stmt
		return ret

INIT_PROC   = "__init__"
ROOT_SCOPES = ["def", "global"]

class Program:
	def __init__(self):
		self.scope = Scope(None) # Definition
	def add(self, name, definition):
		print "adding to program"
		self.scope.add(name, definition)
	def execute(self):
		if self.scope.has_key(INIT_PROC):
			self.scope[INIT_PROC].execute()
		else: print "ERROR: no __init__() procedure found"
	def __str__(self):
		ret = "Program:\n"
		ret += str(self.scope)
		return ret

##### STMT TREE #########
class Statement:
	def __init__(self):
		pass # child-defined
	def execute(self):
		pass # ditto
	def __str__(self):
		ret = "Statement:\n"
		return ret

class Definition(Statement):
	def __init__(self, name, context):
		Statement.__init__(self)
		context.add(name, self)
	def __str__(self):
		ret = "Definition:\n"
		return ret

class Procedure(Definition):
	class FormalParam:
		def __init__(self, type, name):
			self.type = type # Type
			self.name = name # Identifier
		def __str__(self):
			ret = "FormalParam:\n"
			ret += "type: " + str(self.type) + "; name: " + str(self.name) + "\n"
			return ret
	def __init__(self, name, context):
		Definition.__init__(self, name, context)
		self.formalparams = []       # FormalParam
		self.block        = Block()  # Statement
		self.context      = context  # Scope
	def addParam(self, type, name):
		self.formalparams.append(self.FormalParam(type, name))
	def addStmt(self, statement):
		print "stmt added: " + str(statement)
		self.block.add(statement)
	def bind(self, name, value):
		pass # return copy of procedure with name bound to value
	def execute(self, params):
		pass # bind params, execute statements.  stop on "return"
			 # statements can't return, but that's enforced in parsing. 
			 # functions CAN return, and inherit from here.  easier than repeating logic
	def __str__(self):
		ret = "Procedure:\n"
		for parm in self.formalparams:
			ret += str(parm)
		for stmt in self.block.statements:
			ret += str(stmt)
		return ret

class Function(Procedure):
	def __init__(self, type, name, context):
		Procedure.__init__(self, name, context)
		self.returnType = type # Type
	def __str__(self):
		ret = "Function:\n"
		for parm in self.formalparams:
			ret += str(parm)
		return ret

class Expression(Statement):
	class OpElement:
		def __init__(self, operator, rest):
			self.operator   = operator # InfixOperator
			self.rest       = rest     # Expression
			self.eval_type  = None
			self.eval_value = None
	def __init__(self, term):
		Statement.__init__(self)
		self.term       = term # Term
		self.rest       = []   # OpElement
		self.eval_type  = None
		self.eval_value = None
	def append(self, operator, rest):
		self.rest.append(OpElement(operator, rest))
	def evaluate(self):
		pass # evaluate term. for each op, determine compatibility, evaluate next term and combo if possible
		# populate eval_type and eval_value with result

class Cond(Statement):
	class CondElement:
		def __init__(self, cond, block):
			self.cond  = cond  # Expression
			self.block = block # Statement
	def __init__(self):
		Statement.__init__(self)
		self.conds = [] # CondElement
	def append(self, cond, stmts):
		self.conds.append(CondElement(cond, block))
	def execute(self):
		pass # for each element in turn, test cond.  for the first true one, evaluate corresponding block

class While(Statement):
	def __init__(self):
		Statement.__init__(self, cond, block)
		self.cond  = cond  # Expression
		self.block = block # Statement
	def execute(self):
		pass # execute cond, then statements if evaluates to true.  repeat.

class Set(Statement):
	def __init__(self):
		Statement.__init__(self, lvalue, rvalue)
		self.lvalue = lvalue # Variable
		self.rvalue = rvalue # Expression
	def execute(self):
		pass # figure out where lvalue is, and put rvalue there

class RPN(Statement):
	VAR, INFIX, PREFIX, FNKW, OPKW, LITERAL = range(6)
	class RpnAtom:
		def __init__(self, type, content):
			self.type    = type    # from list
			self.content = content # reference/string/value
	def __init__(self):
		Statement.__init__(self)
		self.atoms = [] # RpnAtom
	def append(self, type, content):
		self.atoms.append(RpnAtom(type, content))
	def execute(self):
		pass # do the push/pop/apply thing.

class Call(Statement):
	def __init__(self, name):
		Statement.__init__(self, name)
		self.name   = name # Identifier or KW
		self.params = []   # ActualParam
	def addParam(self, name, expr, scope):
		# retrieve copy of procedure by name from scope
		if name is None:
			name = name
			pass # retrieve first unbound formal param name
		self.params.append(ActualParam(name, expr))
	def execute(self, scope):
		# if unbound params, 
			# copy procedure
			# check stack.  pop and bind left to right
		pass # execute

class Return(Statement):
	def __init__(self):
		Statement.__init__(self, expr)
		self.expr        = expr # Expression
		self.eval_type   = None # Type
		self.eval_value  = None # Value
	def execute(self):
		self.expr.execute()
		pass # populate eval_type and eval_value with result
#########################

##### TERM TREE #########
class Term:
	LITERAL, PREBINDING, INDEXABLE , PREFIXOP= range(4)
	def __init__(self, kind = LITERAL, value = None):
		self.kind        = kind # from list
		self.value       = value   # Value, for literal or expression
		self.eval_type   = None    # Type
		self.eval_value  = None    # Value

class Indexable(Term):
	def __init__(self, expr, index = None):
		Term.__init__(self, Term.INDEXABLE, expr) # Variable, Function Application, or Expression
		self.index = index # Expression
	def execute(self):
		pass # populate eval_type and eval_value with result
		# if result is array and index is present, populate eval_ with element indexed

class Apply(Indexable):
	def __init__(self):
		Indexable.__init__(self, name)
		self.name   = None # Identifier or KW
		self.params = []   # ActualParam
	def addParam(self, name, expr, scope):
		# retrieve copy of procedure by name from scope
		if name is None:
			name = name
			pass # retrieve first unbound formal param name
		self.params.append(ActualParam(name, expr))
	def execute(self, scope):
		# if unbound params, 
			# copy procedure
			# check stack.  pop and bind left to right
		pass # execute and populate eval_type/eval_value
		# if result is array and index is present, populate eval_ with element indexed

class Prefix(Term):
	def __init__(self, operator, expr):
		Term.__init__(self, Term.PREFIXOP)
		self.operator = operator # PrefixOperator
		self.expr     = expr     # Expression
	def execute(self):
		pass # evaluate expression.  apply operator.  populate eval_

class Prebinding(Term):
	def __init__(self):
		Term.__init__(self, Term.PREBINDING)
		self.name      = None # Identifier
		self.params    = []   # ActualParam
		self.eval_sub  = None # Function or Procedure
	def addParam(self, name, expr, scope):
		# retrieve copy of subroutine by name from scope
		if name is None:
			name = name
			pass # retrieve first unbound formal param name
		self.params.append(ActualParam(name, expr))
	def execute(self, scope):
		pass # populate eval_ with modified subroutine
#########################

class ActualParam:
	def __init__(self, name, expr):
		self.name = name # Idenfifier, optional
		self.expr = expr # Expression

class Variable(Definition):
	def __init__(self, name, type, context):
		Definition.__init__(self, name, context)
		self.type  = type        # Type
		self.value = None        # Value
		self.properties = dict() # String-Variable pairs
	def __str__(self):
		ret = "Variable:\n"
		return ret

