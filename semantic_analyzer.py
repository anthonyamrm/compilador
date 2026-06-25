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

    # ─── Uso de identificadores ──────────────────────────────────

    def visitPrimary(self, ctx):
        ident_tok = ctx.IDENT()
        if ident_tok is not None:
            nome = ident_tok.getText()
            linha = ident_tok.symbol.line
            is_new = ctx.getChild(0).getText() == 'new'
            info = self.lookup(nome)
            if info is None:
                if is_new:
                    self.errors.add_error(linha, f"classe '{nome}' não declarada")
                else:
                    self.errors.add_error(linha, f"identificador '{nome}' não declarado")
            elif is_new and info.get('categoria') != 'class':
                self.errors.add_error(linha, f"'{nome}' não é uma classe")
        return self.visitChildren(ctx)

    def visitPostfixExpr(self, ctx):
        if ctx.argList() is not None:
            self._check_call(ctx)
        elif ctx.IDENT() is not None:
            self._check_member_access(ctx)
        return self.visitChildren(ctx)

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
