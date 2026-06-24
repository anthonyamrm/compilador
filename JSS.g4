grammar JSS;

// ─── Regras sintáticas ────────────────────────────────────────────────────────

program
    : topDecl* EOF
    ;

topDecl
    : functionDecl
    | classDecl
    | varDecl
    | constDecl
    ;

// Funções

functionDecl
    : 'function' type IDENT '(' params ')' block
    ;

params
    : param (',' param)*
    |
    ;

param
    : type IDENT
    ;

// Classes

classDecl
    : 'class' IDENT '{' classMember* '}'
    ;

classMember
    : constructorDecl
    | methodDecl
    | attrDecl
    ;

constructorDecl
    : IDENT 'constructor' '(' params ')' block
    ;

methodDecl
    : type IDENT '(' params ')' block
    ;

attrDecl
    : type IDENT ';'
    ;

// Tipos

type
    : 'int'
    | 'real'
    | 'str'
    | 'bool'
    | 'void'
    ;

// Bloco e statements

block
    : '{' statement* '}'
    ;

statement
    : varDecl
    | constDecl
    | returnStmt
    | ifStmt
    | whileStmt
    | forStmt
    | breakStmt
    | exprStmt
    ;

varDecl
    : 'let' type ('[' INT_LIT ']')? declarator (',' declarator)* ';'
    ;

varDeclNoSemi
    : 'let' type ('[' INT_LIT ']')? declarator (',' declarator)*
    ;

declarator
    : IDENT ('=' expr)?
    ;

constDecl
    : 'const' type IDENT '=' expr ';'
    ;

returnStmt
    : 'return' expr? ';'
    ;

ifStmt
    : 'if' '(' expr ')' block ('else' elseClause)?
    ;

elseClause
    : ifStmt
    | block
    ;

whileStmt
    : 'while' '(' expr ')' block
    ;

forStmt
    : 'for' '(' forInit? ';' expr? ';' expr? ')' block
    ;

forInit
    : varDeclNoSemi
    | expr
    ;

breakStmt
    : 'break' ';'
    ;

exprStmt
    : expr ';'
    ;

// ─── Expressões (precedência via regras encadeadas) ───────────────────────────

expr
    : orExpr (assignOp expr)?
    ;

assignOp
    : '=' | '+=' | '-=' | '*=' | '/=' | '%='
    ;

orExpr
    : orExpr '||' andExpr
    | andExpr
    ;

andExpr
    : andExpr '&&' cmpExpr
    | cmpExpr
    ;

cmpExpr
    : cmpExpr cmpOp addExpr
    | addExpr
    ;

cmpOp
    : '==' | '!=' | '<=' | '>=' | '<' | '>'
    ;

addExpr
    : addExpr '+' mulExpr
    | addExpr '-' mulExpr
    | mulExpr
    ;

mulExpr
    : mulExpr '*' powExpr
    | mulExpr '/' powExpr
    | mulExpr '%' powExpr
    | powExpr
    ;

powExpr
    : unaryExpr '**' powExpr
    | unaryExpr
    ;

unaryExpr
    : '!'  unaryExpr
    | '-'  unaryExpr
    | '+'  unaryExpr
    | '++' unaryExpr
    | '--' unaryExpr
    | postfixExpr
    ;

postfixExpr
    : postfixExpr '[' expr ']'
    | postfixExpr '(' argList ')'
    | postfixExpr '.' IDENT
    | primary
    ;

argList
    : expr (',' expr)*
    |
    ;

primary
    : INT_LIT
    | REAL_LIT
    | STR_LIT
    | 'true'
    | 'false'
    | 'null'
    | 'this'
    | IDENT
    | 'new' IDENT '(' argList ')'
    | type '(' expr ')'
    | '(' expr ')'
    | '[' (expr (',' expr)*)? ']'
    ;

// ─── Terminais (léxico) ───────────────────────────────────────────────────────

REAL_LIT
    : [0-9]+ ('.' [0-9]+)? [Ee] [+-]? [0-9]+
    | [0-9]+ '.' [0-9]+
    ;

INT_LIT
    : [0-9]+
    ;

STR_LIT
    : '"' (~["\\\r\n] | '\\' .)* '"'
    ;

IDENT
    : [a-zA-Z_] [a-zA-Z0-9_]*
    ;

LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

WS
    : [ \t\r\n]+ -> skip
    ;
