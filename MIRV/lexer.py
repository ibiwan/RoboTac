#!/usr/bin/env python
import sys, re

keywords    = ['return', 'cond', 'while',   'apply',    'call',   'func',   'proc',  'rpn',
               'global',  'def', 'local',     'let',     'set',    'int',   'real', 'char', 'array', 'matrix',
               'and',      'or',   'not',     'sin',     'cos',    'tan',   'asin', 'acos',  'atan',  'atan2', 'sqrt',
               'true',  'false', 'empty', 'invalid', '_error_', '_init_', '_loop_']

operators   = [('+',  'PLUS'),  ('-',  'MINUS'), ('*',  'TIMES'), ('/',  'DIV'), ('%', 'MOD'),  ('++', 'INCR'), ('--', 'DECR'),
               ('=', 'ASSIGN'), ('<',  'LT'),    ('<=', 'LTE'),   ('==', 'EQ'),  ('>=', 'GTE'), ('>', 'GT'), 
               ('<<', 'SHL'),   ('>>', 'SHR'),   ('&',  'BAND'),  ('|',  'BOR'), ('^', 'BXOR'), ('~',  'BNOT')]

structurers = [('(', 'LPAREN'), (')', 'RPAREN'), ('{', 'LBRACE'), ('}', 'RBRACE'), ('[', 'LBRACKET'), (']', 'RBRACKET'), 
               (';', 'SEMI'),   ('@', 'ATSIGN'), (',', 'COMMA')]

relex = r"[a-zA-Z_]\w*"
def lexeme (scanner, token): 
	for kw in keywords:
		if kw == token: return kw.upper(), None
	return "ID",   token

reop = r"[=+\-*/<>%&|^~]+"
def operator (scanner, token):
	for op in operators:
		if op[0] == token: return op[1], None
	err("Invalid operator, ignored: \"" + token + "\"")

renum = r"[0-9]+(\.[0-9]*)?|[0-9]*\.[0-9]+" # 5, 1., .4, 3.7 are all valid
def number (scanner, token):
	try:    return "INT",  int(token)
	except: return "REAL", float(token)

restrc = r"[(){}\[\];@,]"
def struct (scanner, token):
	for sym in structurers:
		if sym[0] == token: return sym[1], None
	err("Lexer is inconsistent; check structuring characters")
 
recomm = r"//.*$"
def comment (scanner, token):
	print "Comment Line " + str(lineno) + ": " + token

redstr = r'".*?"'
def string (scanner, token):
	return "STRING", token[1:-1]

resstr = r"'.*?'"
def string (scanner, token):
	return "STRING", token[1:-1]

scanner = re.Scanner([
    (relex,   lexeme), # id or keyword
    (recomm, comment), # comment to end of line
    (reop,  operator), # prefix or infix
    (renum,   number), # int or real
    (restrc,  struct), # program structure
    (redstr,  string), # string in double quotes
    (resstr,  string), # string in single quotes
    (r"\s+",    None), # whitespace
    ])
 
lineno = -1;
def err(txt):
	print "ERROR Line " + str(lineno) + ": " + txt

def lexer(file):
	global lineno
	lineno = 1
	for line in file:
		print "\n\nLine " + str(lineno) + ":\t\t" + line
		tokens, remainder = scanner.scan(line)
		if remainder: err("Invalid token(s), ignored: \"" + remainder + "\"")
		for token in tokens:
			yield token # makes this into a generator
		lineno += 1

for token in lexer(sys.stdin):
	print token