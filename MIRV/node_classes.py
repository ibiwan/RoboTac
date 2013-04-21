#!/usr/bin/env python
class Type:
	INT, REAL, STRING, ARRAY = range(4)

class Operator:
	PLUS, MINUS, TIMES, DIVIDE = range(4)

class Program:
	def __init__(self):
		self.definitions = [] # Definition

class Statement:
	def __init__(self):
		pass

class Definition(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.scope = None # Scope
		self.name  = None # Identifier

class ProcDef(Definition):
	def __init__(self):
		Definition.__init__(self)
		self.formalparams = [] # FormalParam
		self.block        = [] # Statement

class FuncDef(ProcDef):
	def __init__(self):
		ProcDef.__init__(self)
		self.returnType = None # Type

class VarDef(Definition):
	def __init__(self):
		Definition.__init__(self)
		self.type       = None # Type
		self.expression = None # Expression

class Expression(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.term        = None # Term
		self.operator    = None # InfixOperator, optional
		self.rest        = None # Term, optional
		self.eval_type   = None # Type
		self.eval_value  = None # Value

class CondElement:
	def __init__(self):
		self.cond = None # Expression
		self.block = []  # Statement

class Cond(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.conds = [] # CondElement

class While(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.cond = None # Expression
		self.block = []  # Statement

class Set(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.lvalue = None # Variable
		self.rvalue = None # Expression

class RpnAtom:
	VAR, INFIX, PREFIX, FNKW, OPKW, LITERAL = range(6)
	def __init__(self):
		self.type = None    # from list
		self.content = None # one of the above types

class RPN(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.atoms = [] # RpnAtom

class Call(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.name = None # Identifier or KW
		self.params = [] # ActualParam

class Return(Statement):
	def __init__(self):
		Statement.__init__(self)
		self.ret =         None # Expression
		self.eval_type   = None # Type
		self.eval_value  = None # Value

class Term:
	LITERAL, PREBINDING, INDEXABLE = range(3)
	def __init__(self):
		self.term_type =   None # from list
		self.value =       None # Value, for literal
		self.eval_type   = None # Type
		self.eval_value  = None # Value

class Indexable(Term):
	def __init__(self):
		Term.__init__(self)
		self.term_type = Term.INDEXABLE
		# self.value from Term
		self.index = None      # Expression

class Variable(Indexable):
	def __init__(self):
		Indexable.__init__(self)
		self.type = None         # Type
		self.value = None        # Value
		self.name = None         # Identifier
		self.properties = dict() # String-Variable pairs

class Apply(Indexable):
	def __init__(self):
		Indexable.__init__(self)
		self.name = None # Identifier or KW
		self.params = [] # ActualParam

class Prefix(Indexable):
	def __init__(self):
		Indexable.__init__(self)
		self.operator = None # PrefixOperator
		self.expr = None     # Expression

class Group(Indexable):
	def __init__(self):
		Indexable.__init__(self)		
		self.expr = None # Expression

class FormalParam:
	def __init__(self):
		self.type = None # Type
		self.name = None # Identifier

class ActualParam:
	def __init__(self):
		self.name = None # Idenfifier, optional
		self.expr = None # Expression

class Prebinding(Term):
	def __init__(self):
		Term.__init__(self)
		self.term_type = Term.PREBINDING
		self.name = None # Identifier
		self.params = [] # ActualParam
