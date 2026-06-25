from JSSVisitor import JSSVisitor
from error_listener import JSSErrorListener


class SemanticAnalyzer(JSSVisitor):
    BUILTINS = {
        'input': {'categoria': 'builtin_function'},
        'console': {'categoria': 'builtin_obj', 'membros': {'log'}},
    }

    def __init__(self):
        super().__init__()
        self.scopes = [{}]
        self.errors = JSSErrorListener('Semântico')
        self._function_stack = []
        self._register_builtins()

    # ─── Pilha de escopos ─────────────────────────────────────────

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def current_scope(self):
        return self.scopes[-1]

    def declare(self, name, info, line):
        if name in self.current_scope():
            self.errors.add_error(
                line, f"identificador '{name}' já declarado neste escopo"
            )
            return False
        self.current_scope()[name] = info
        return True

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # ─── Helpers ─────────────────────────────────────────────────

    def _build_type(self, type_ctx, dims):
        base = type_ctx.getText()
        return base + '[]' * len(dims)

    def _register_builtins(self):
        for nome, info in self.BUILTINS.items():
            self.scopes[0][nome] = info

    # ─── Ponto de entrada ─────────────────────────────────────────

    def analyze(self, tree):
        self._collect_globals(tree)
        self.visit(tree)
        return self.errors

    def _collect_globals(self, tree):
        for top in tree.topDecl():
            if top.functionDecl() is not None:
                self._declare_function(top.functionDecl())
            elif top.classDecl() is not None:
                self._declare_class(top.classDecl())

    def _declare_function(self, ctx):
        ident_tok = ctx.IDENT()
        nome = ident_tok.getText()
        tipo_retorno = self._build_type(ctx.type_(), ctx.INT_LIT())
        param_types = []
        if ctx.params() is not None:
            for p in ctx.params().param():
                param_types.append(self._build_type(p.type_(), p.INT_LIT()))
        self.declare(
            nome,
            {
                'categoria': 'function',
                'tipo_retorno': tipo_retorno,
                'params': param_types,
            },
            ident_tok.symbol.line,
        )

    def _declare_class(self, ctx):
        ident_tok = ctx.IDENT()
        nome = ident_tok.getText()
        self.declare(
            nome,
            {'categoria': 'class'},
            ident_tok.symbol.line,
        )

    # ─── Escopos: bloco, função, for ─────────────────────────────

    def visitBlock(self, ctx):
        self.push_scope()
        self.visitChildren(ctx)
        self.pop_scope()
        return None

    def _enter_callable(self, params_ctx, block_ctx, tipo_retorno, nome, linha, kind):
        self._function_stack.append({
            'tipo_retorno': tipo_retorno,
            'nome': nome,
            'linha': linha,
            'kind': kind,
            'has_return_expr': False,
        })
        self.push_scope()
        if params_ctx is not None:
            for p in params_ctx.param():
                ident_tok = p.IDENT()
                p_nome = ident_tok.getText()
                p_tipo = p.type_().getText()
                self.declare(
                    p_nome,
                    {'categoria': 'param', 'tipo': p_tipo},
                    ident_tok.symbol.line,
                )
        self.visit(block_ctx)
        self.pop_scope()

        func = self._function_stack.pop()
        if func['tipo_retorno'] != 'void' and not func['has_return_expr']:
            self.errors.add_error(
                func['linha'],
                f"função '{func['nome']}' deve retornar um valor do tipo '{func['tipo_retorno']}'"
            )

    def visitFunctionDecl(self, ctx):
        ident_tok = ctx.IDENT()
        nome = ident_tok.getText()
        tipo_retorno = self._build_type(ctx.type_(), ctx.INT_LIT())
        self._enter_callable(
            ctx.params(), ctx.block(),
            tipo_retorno, nome, ident_tok.symbol.line, 'function',
        )
        return None

    def visitConstructorDecl(self, ctx):
        ident_tok = ctx.IDENT()
        nome = ident_tok.getText()
        self._enter_callable(
            ctx.params(), ctx.block(),
            'void', nome, ident_tok.symbol.line, 'constructor',
        )
        return None

    def visitMethodDecl(self, ctx):
        ident_tok = ctx.IDENT()
        nome = ident_tok.getText()
        tipo_retorno = self._build_type(ctx.type_(), ctx.INT_LIT())
        self._enter_callable(
            ctx.params(), ctx.block(),
            tipo_retorno, nome, ident_tok.symbol.line, 'method',
        )
        return None

    def visitForStmt(self, ctx):
        self.push_scope()
        self.visitChildren(ctx)
        self.pop_scope()
        return None

    def visitReturnStmt(self, ctx):
        linha = ctx.start.line
        has_expr = ctx.expr() is not None

        if not self._function_stack:
            self.errors.add_error(linha, "'return' fora de uma função")
            return self.visitChildren(ctx)

        current = self._function_stack[-1]
        if current['tipo_retorno'] == 'void' and has_expr:
            if current['kind'] == 'constructor':
                self.errors.add_error(linha, "construtor não pode retornar um valor")
            else:
                self.errors.add_error(linha, "função 'void' não pode retornar um valor")
        elif current['tipo_retorno'] != 'void' and not has_expr:
            self.errors.add_error(
                linha,
                f"'return' sem valor em função com tipo de retorno '{current['tipo_retorno']}'"
            )

        if has_expr:
            current['has_return_expr'] = True

        return self.visitChildren(ctx)

    # ─── Declarações de variável e constante ─────────────────────

    def visitVarDecl(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        for d in ctx.declarator():
            ident_tok = d.IDENT()
            nome = ident_tok.getText()
            self.declare(
                nome,
                {'categoria': 'var', 'tipo': tipo},
                ident_tok.symbol.line,
            )
            if d.expr() is not None:
                self.visit(d.expr())
        return None

    def visitVarDeclNoSemi(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        for d in ctx.declarator():
            ident_tok = d.IDENT()
            nome = ident_tok.getText()
            self.declare(
                nome,
                {'categoria': 'var', 'tipo': tipo},
                ident_tok.symbol.line,
            )
            if d.expr() is not None:
                self.visit(d.expr())
        return None

    def visitConstDecl(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        ident_tok = ctx.IDENT()
        nome = ident_tok.getText()
        self.declare(
            nome,
            {'categoria': 'const', 'tipo': tipo},
            ident_tok.symbol.line,
        )
        self.visit(ctx.expr())
        return None

    # ─── Sistema de tipos: helpers ───────────────────────────────

    def _is_numeric(self, t):
        return t in ('int', 'real')

    def _is_primitive(self, t):
        return t in ('int', 'real', 'str', 'bool')

    def _check_arith_binop(self, ctx, left, right, op):
        if '?' in (left, right):
            return '?'
        line = ctx.start.line
        if op == '+' and (left == 'str' or right == 'str'):
            other = right if left == 'str' else left
            if self._is_primitive(other):
                return 'str'
            self.errors.add_error(line, f"operador '+' não pode concatenar 'str' com '{other}'")
            return '?'
        if not (self._is_numeric(left) and self._is_numeric(right)):
            self.errors.add_error(line, f"operador '{op}' requer operandos numéricos, recebeu '{left}' e '{right}'")
            return '?'
        if 'real' in (left, right):
            return 'real'
        return 'int'

    def _check_int_binop(self, ctx, left, right, op):
        if '?' in (left, right):
            return '?'
        if left != 'int' or right != 'int':
            self.errors.add_error(ctx.start.line, f"operador '{op}' requer operandos 'int', recebeu '{left}' e '{right}'")
            return '?'
        return 'int'

    def _check_rel_binop(self, ctx, left, right, op):
        if '?' in (left, right):
            return '?'
        line = ctx.start.line
        if left.endswith('[]') or right.endswith('[]'):
            self.errors.add_error(line, f"operador '{op}' não pode ser aplicado em vetores")
            return '?'
        if not (self._is_primitive(left) and self._is_primitive(right)):
            self.errors.add_error(line, f"operador '{op}' requer operandos primitivos, recebeu '{left}' e '{right}'")
            return '?'
        if left == right or (self._is_numeric(left) and self._is_numeric(right)):
            return 'bool'
        self.errors.add_error(line, f"operador '{op}' requer operandos de mesmo tipo, recebeu '{left}' e '{right}'")
        return '?'

    def _check_eq_binop(self, ctx, left, right, op):
        if '?' in (left, right):
            return '?'
        if left == right:
            return 'bool'
        if self._is_numeric(left) and self._is_numeric(right):
            return 'bool'
        if 'null' in (left, right):
            return 'bool'
        self.errors.add_error(ctx.start.line, f"operador '{op}' requer operandos compatíveis, recebeu '{left}' e '{right}'")
        return '?'

    def _check_logical_binop(self, ctx, left, right, op):
        if '?' in (left, right):
            return '?'
        if left != 'bool' or right != 'bool':
            self.errors.add_error(ctx.start.line, f"operador '{op}' requer operandos 'bool', recebeu '{left}' e '{right}'")
            return '?'
        return 'bool'

    def _check_unary_op(self, ctx, operand, op):
        if operand == '?':
            return '?'
        line = ctx.start.line
        if op == '!':
            if operand != 'bool':
                self.errors.add_error(line, f"operador '!' requer operando 'bool', recebeu '{operand}'")
                return '?'
            return 'bool'
        if not self._is_numeric(operand):
            self.errors.add_error(line, f"operador unário '{op}' requer operando numérico, recebeu '{operand}'")
            return '?'
        return operand

    def _infer_call_return_type(self, callee_ctx):
        if callee_ctx is None or callee_ctx.primary() is None:
            return '?'
        primary = callee_ctx.primary()
        if primary.IDENT() is None:
            return '?'
        if primary.getChild(0).getText() == 'new':
            return '?'
        info = self.lookup(primary.IDENT().getText())
        if info is None:
            return '?'
        if info.get('categoria') == 'function':
            return info.get('tipo_retorno', '?')
        return '?'

    # ─── Expressões: cadeia que devolve tipo + valida operadores ─

    def visitExpr(self, ctx):
        if ctx.assignOp() is None:
            return self.visit(ctx.orExpr())
        self.visit(ctx.orExpr())
        return self.visit(ctx.expr())

    def visitOrExpr(self, ctx):
        if ctx.orExpr() is None:
            return self.visit(ctx.andExpr())
        left = self.visit(ctx.orExpr())
        right = self.visit(ctx.andExpr())
        return self._check_logical_binop(ctx, left, right, '||')

    def visitAndExpr(self, ctx):
        if ctx.andExpr() is None:
            return self.visit(ctx.cmpExpr())
        left = self.visit(ctx.andExpr())
        right = self.visit(ctx.cmpExpr())
        return self._check_logical_binop(ctx, left, right, '&&')

    def visitCmpExpr(self, ctx):
        if ctx.cmpExpr() is None:
            return self.visit(ctx.addExpr())
        left = self.visit(ctx.cmpExpr())
        right = self.visit(ctx.addExpr())
        op = ctx.cmpOp().getText()
        if op in ('==', '!='):
            return self._check_eq_binop(ctx, left, right, op)
        return self._check_rel_binop(ctx, left, right, op)

    def visitAddExpr(self, ctx):
        if ctx.addExpr() is None:
            return self.visit(ctx.mulExpr())
        left = self.visit(ctx.addExpr())
        right = self.visit(ctx.mulExpr())
        op = ctx.getChild(1).getText()
        return self._check_arith_binop(ctx, left, right, op)

    def visitMulExpr(self, ctx):
        if ctx.mulExpr() is None:
            return self.visit(ctx.powExpr())
        left = self.visit(ctx.mulExpr())
        right = self.visit(ctx.powExpr())
        op = ctx.getChild(1).getText()
        if op == '%':
            return self._check_int_binop(ctx, left, right, op)
        return self._check_arith_binop(ctx, left, right, op)

    def visitPowExpr(self, ctx):
        if ctx.powExpr() is None:
            return self.visit(ctx.unaryExpr())
        left = self.visit(ctx.unaryExpr())
        right = self.visit(ctx.powExpr())
        return self._check_int_binop(ctx, left, right, '**')

    def visitUnaryExpr(self, ctx):
        if ctx.postfixExpr() is not None:
            return self.visit(ctx.postfixExpr())
        op = ctx.getChild(0).getText()
        operand = self.visit(ctx.unaryExpr())
        return self._check_unary_op(ctx, operand, op)

    # ─── Uso de identificadores ──────────────────────────────────

    def visitPrimary(self, ctx):
        if ctx.INT_LIT() is not None:
            return 'int'
        if ctx.REAL_LIT() is not None:
            return 'real'
        if ctx.STR_LIT() is not None:
            return 'str'

        first_text = ctx.getChild(0).getText() if ctx.getChildCount() > 0 else ''

        if first_text in ('true', 'false'):
            return 'bool'
        if first_text == 'null':
            return 'null'
        if first_text == 'this':
            return 'this'

        if first_text == 'new':
            ident_tok = ctx.IDENT()
            nome = ident_tok.getText()
            linha = ident_tok.symbol.line
            info = self.lookup(nome)
            if info is None:
                self.errors.add_error(linha, f"classe '{nome}' não declarada")
                if ctx.argList() is not None:
                    self.visit(ctx.argList())
                return '?'
            if info.get('categoria') != 'class':
                self.errors.add_error(linha, f"'{nome}' não é uma classe")
                if ctx.argList() is not None:
                    self.visit(ctx.argList())
                return '?'
            if ctx.argList() is not None:
                self.visit(ctx.argList())
            return nome

        if ctx.IDENT() is not None:
            ident_tok = ctx.IDENT()
            nome = ident_tok.getText()
            linha = ident_tok.symbol.line
            info = self.lookup(nome)
            if info is None:
                self.errors.add_error(linha, f"identificador '{nome}' não declarado")
                return '?'
            cat = info.get('categoria')
            if cat in ('var', 'const', 'param'):
                return info.get('tipo', '?')
            return '?'

        if ctx.castType() is not None:
            self.visit(ctx.expr(0))
            return ctx.castType().getText()

        if first_text == '(':
            return self.visit(ctx.expr(0))

        if first_text == '[':
            exprs = ctx.expr()
            if not exprs:
                return '?[]'
            elem_types = [self.visit(e) for e in exprs]
            first = elem_types[0]
            if first != '?' and all(t == first for t in elem_types):
                return f'{first}[]'
            return '?[]'

        return '?'

    def visitPostfixExpr(self, ctx):
        if ctx.primary() is not None:
            return self.visit(ctx.primary())

        if ctx.argList() is not None:
            self._check_call(ctx)
            self.visit(ctx.argList())
            return self._infer_call_return_type(ctx.postfixExpr())

        if ctx.IDENT() is not None:
            self._check_member_access(ctx)
            self.visit(ctx.postfixExpr())
            return '?'

        if ctx.expr() is not None:
            base_type = self.visit(ctx.postfixExpr())
            self.visit(ctx.expr())
            if base_type and base_type.endswith('[]'):
                return base_type[:-2]
            return '?'

        return '?'

    def _check_call(self, ctx):
        callee = ctx.postfixExpr()
        if callee is None or callee.primary() is None:
            return
        primary = callee.primary()
        if primary.IDENT() is None:
            return
        if primary.getChild(0).getText() == 'new':
            return

        ident_tok = primary.IDENT()
        nome = ident_tok.getText()
        linha = ident_tok.symbol.line
        info = self.lookup(nome)
        if info is None:
            return

        categoria = info.get('categoria')
        if categoria in ('function', 'builtin_function'):
            return
        if categoria == 'class':
            self.errors.add_error(
                linha,
                f"para criar um objeto da classe '{nome}', use 'new {nome}(...)'"
            )
        else:
            self.errors.add_error(
                linha,
                f"'{nome}' não é uma função e não pode ser chamada"
            )

    def _check_member_access(self, ctx):
        base = ctx.postfixExpr()
        member_tok = ctx.IDENT()
        if base is None or base.primary() is None:
            return
        primary = base.primary()
        if primary.IDENT() is None:
            return
        if primary.getChild(0).getText() == 'new':
            return

        obj_name = primary.IDENT().getText()
        info = self.lookup(obj_name)
        if info is None:
            return

        if info.get('categoria') == 'builtin_obj':
            member = member_tok.getText()
            linha = member_tok.symbol.line
            membros = info.get('membros', set())
            if member not in membros:
                self.errors.add_error(
                    linha,
                    f"'{obj_name}' não possui o membro '{member}'"
                )
