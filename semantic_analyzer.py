from JSSVisitor import JSSVisitor
from JSSParser import JSSParser
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
        self._loop_depth = 0
        self._class_stack = []
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
        if tipo_retorno.endswith('[]'):
            self.errors.add_error(
                ident_tok.symbol.line,
                f"função '{nome}' não pode ter tipo de retorno vetor ('{tipo_retorno}')"
            )
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
        linha = ident_tok.symbol.line

        atributos = {}
        metodos = {}
        constructor = None
        seen_method_or_ctor = False

        for member in ctx.classMember():
            if member.attrDecl() is not None:
                attr = member.attrDecl()
                attr_tok = attr.IDENT()
                attr_nome = attr_tok.getText()
                attr_tipo = self._build_type(attr.type_(), attr.INT_LIT())
                attr_linha = attr_tok.symbol.line
                if seen_method_or_ctor:
                    self.errors.add_error(
                        attr_linha,
                        f"atributo '{attr_nome}' declarado depois de método/construtor (atributos devem vir primeiro)"
                    )
                if attr_nome in atributos:
                    self.errors.add_error(attr_linha, f"atributo '{attr_nome}' já declarado na classe '{nome}'")
                else:
                    atributos[attr_nome] = attr_tipo
            elif member.constructorDecl() is not None:
                seen_method_or_ctor = True
                ctor = member.constructorDecl()
                ctor_tok = ctor.IDENT()
                ctor_class_name = ctor_tok.getText()
                ctor_linha = ctor_tok.symbol.line
                if ctor_class_name != nome:
                    self.errors.add_error(
                        ctor_linha,
                        f"constructor deve ter o nome da classe '{nome}', encontrado '{ctor_class_name}'"
                    )
                if constructor is not None:
                    self.errors.add_error(ctor_linha, f"construtor da classe '{nome}' já declarado")
                else:
                    param_types = []
                    if ctor.params() is not None:
                        for p in ctor.params().param():
                            param_types.append(self._build_type(p.type_(), p.INT_LIT()))
                    constructor = {'params': param_types}
            elif member.methodDecl() is not None:
                seen_method_or_ctor = True
                m = member.methodDecl()
                m_tok = m.IDENT()
                m_nome = m_tok.getText()
                m_linha = m_tok.symbol.line
                m_tipo = self._build_type(m.type_(), m.INT_LIT())
                if m_tipo.endswith('[]'):
                    self.errors.add_error(
                        m_linha,
                        f"método '{m_nome}' não pode ter tipo de retorno vetor ('{m_tipo}')"
                    )
                if m_nome in metodos or m_nome in atributos:
                    self.errors.add_error(m_linha, f"membro '{m_nome}' já declarado na classe '{nome}'")
                else:
                    param_types = []
                    if m.params() is not None:
                        for p in m.params().param():
                            param_types.append(self._build_type(p.type_(), p.INT_LIT()))
                    metodos[m_nome] = {'tipo_retorno': m_tipo, 'params': param_types}

        if constructor is None:
            self.errors.add_error(linha, f"classe '{nome}' não declara um constructor")

        self.declare(
            nome,
            {
                'categoria': 'class',
                'atributos': atributos,
                'metodos': metodos,
                'constructor': constructor,
            },
            linha,
        )

    # ─── Escopos: bloco, função, for ─────────────────────────────

    def visitBlock(self, ctx):
        self.push_scope()
        self.visitChildren(ctx)
        self.pop_scope()
        return None

    def visitClassDecl(self, ctx):
        nome = ctx.IDENT().getText()
        self._class_stack.append(nome)
        self.visitChildren(ctx)
        self._class_stack.pop()
        return None

    def _extract_lvalue_from_expr(self, expr_ctx):
        if expr_ctx.assignOp() is not None:
            return None
        return self._extract_lvalue(expr_ctx.orExpr())

    def _is_lvalue_postfix(self, postfix_ctx):
        if postfix_ctx.argList() is not None:
            return False
        if postfix_ctx.expr() is not None:
            return True
        if postfix_ctx.IDENT() is not None:
            return True
        if postfix_ctx.primary() is None:
            return False
        primary = postfix_ctx.primary()
        if primary.IDENT() is None:
            return False
        if primary.getChild(0).getText() == 'new':
            return False
        info = self.lookup(primary.IDENT().getText())
        if info is None:
            return False
        return info.get('categoria') in ('var', 'param')

    def _validate_input_args(self, call_ctx, arg_types):
        if call_ctx.argList() is None:
            return
        args = call_ctx.argList().expr()
        for i, (e, t) in enumerate(zip(args, arg_types)):
            lvalue = self._extract_lvalue_from_expr(e)
            if lvalue is None or not self._is_lvalue_postfix(lvalue):
                self.errors.add_error(
                    e.start.line,
                    f"argumento {i+1} de 'input' deve ser uma variável"
                )
                continue
            if t != '?' and t not in ('int', 'real', 'str'):
                self.errors.add_error(
                    e.start.line,
                    f"argumento {i+1} de 'input' deve ser 'int', 'real' ou 'str', recebeu '{t}'"
                )

    def _validate_console_log_args(self, call_ctx, arg_types):
        if call_ctx.argList() is None:
            return
        args = call_ctx.argList().expr()
        for i, (e, t) in enumerate(zip(args, arg_types)):
            if t == '?':
                continue
            if not self._is_primitive(t):
                self.errors.add_error(
                    e.start.line,
                    f"argumento {i+1} de 'console.log': tipo '{t}' não pode ser impresso diretamente (converta com str())"
                )

    def _check_args(self, ctx, expected, actual, what):
        line = ctx.start.line
        if len(expected) != len(actual):
            self.errors.add_error(
                line,
                f"{what} espera {len(expected)} argumento(s), recebeu {len(actual)}"
            )
            return
        for i, (e, a) in enumerate(zip(expected, actual)):
            if not self._is_assignable(e, a):
                self.errors.add_error(
                    line,
                    f"argumento {i+1} de {what}: esperado '{e}', recebeu '{a}'"
                )

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
                p_tipo = self._build_type(p.type_(), p.INT_LIT())
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

    def _check_cond_is_bool(self, expr_ctx, where):
        cond_type = self.visit(expr_ctx)
        if cond_type not in ('bool', '?'):
            self.errors.add_error(
                expr_ctx.start.line,
                f"condição de '{where}' deve ser 'bool', recebeu '{cond_type}'"
            )

    def _for_parts(self, ctx):
        cond = None
        update = None
        semi = 0
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if child.getText() == ';':
                semi += 1
                continue
            if isinstance(child, JSSParser.ExprContext):
                if semi == 1:
                    cond = child
                elif semi == 2:
                    update = child
        return cond, update

    def visitIfStmt(self, ctx):
        self._check_cond_is_bool(ctx.expr(), 'if')
        self.visit(ctx.block())
        if ctx.elseClause() is not None:
            self.visit(ctx.elseClause())
        return None

    def visitWhileStmt(self, ctx):
        self._check_cond_is_bool(ctx.expr(), 'while')
        self._loop_depth += 1
        self.visit(ctx.block())
        self._loop_depth -= 1
        return None

    def visitForStmt(self, ctx):
        self.push_scope()
        self._loop_depth += 1

        if ctx.forInit() is not None:
            self.visit(ctx.forInit())

        cond, update = self._for_parts(ctx)
        if cond is not None:
            self._check_cond_is_bool(cond, 'for')
        if update is not None:
            self.visit(update)

        self.visit(ctx.block())

        self._loop_depth -= 1
        self.pop_scope()
        return None

    def visitBreakStmt(self, ctx):
        if self._loop_depth == 0:
            self.errors.add_error(ctx.start.line, "'break' fora de um loop")
        return None

    def visitReturnStmt(self, ctx):
        linha = ctx.start.line
        has_expr = ctx.expr() is not None
        expr_type = self.visit(ctx.expr()) if has_expr else None

        if not self._function_stack:
            self.errors.add_error(linha, "'return' fora de uma função")
            return None

        current = self._function_stack[-1]
        declared = current['tipo_retorno']

        if declared == 'void' and has_expr:
            if current['kind'] == 'constructor':
                self.errors.add_error(linha, "construtor não pode retornar um valor")
            else:
                self.errors.add_error(linha, "função 'void' não pode retornar um valor")
        elif declared != 'void' and not has_expr:
            self.errors.add_error(
                linha,
                f"'return' sem valor em função com tipo de retorno '{declared}'"
            )
        elif has_expr and declared != 'void':
            if not self._is_assignable(declared, expr_type):
                self.errors.add_error(
                    linha,
                    f"'return' de tipo '{expr_type}' incompatível com retorno declarado '{declared}' de '{current['nome']}'"
                )

        if has_expr:
            current['has_return_expr'] = True

        return None

    # ─── Declarações de variável e constante ─────────────────────

    def _declare_with_init(self, categoria, ctx_type, dims, declarators):
        tipo = self._build_type(ctx_type, dims)
        for d in declarators:
            ident_tok = d.IDENT()
            nome = ident_tok.getText()
            self.declare(
                nome,
                {'categoria': categoria, 'tipo': tipo},
                ident_tok.symbol.line,
            )
            if d.expr() is not None:
                init_type = self.visit(d.expr())
                if not self._is_assignable(tipo, init_type):
                    self.errors.add_error(
                        d.start.line,
                        f"não é possível inicializar '{nome}' (tipo '{tipo}') com valor do tipo '{init_type}'"
                    )

    def visitVarDecl(self, ctx):
        self._declare_with_init('var', ctx.type_(), ctx.INT_LIT(), ctx.declarator())
        return None

    def visitVarDeclNoSemi(self, ctx):
        self._declare_with_init('var', ctx.type_(), ctx.INT_LIT(), ctx.declarator())
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
        init_type = self.visit(ctx.expr())
        if not self._is_assignable(tipo, init_type):
            self.errors.add_error(
                ctx.start.line,
                f"não é possível inicializar constante '{nome}' (tipo '{tipo}') com valor do tipo '{init_type}'"
            )
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
            if left == 'str' and right == 'str':
                return 'str'
            other = right if left == 'str' else left
            self.errors.add_error(line, f"operador '+' requer dois operandos 'str' para concatenação, recebeu '{left}' e '{right}'")
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

    def _is_assignable(self, target, value):
        if '?' in (target, value):
            return True
        if target == value:
            return True
        if target == 'real' and value == 'int':
            return True
        if value == 'null' and not self._is_primitive(target) and target != 'null':
            return True
        if 'this' in (target, value):
            return True
        return False

    def _extract_lvalue(self, or_ctx):
        if or_ctx.orExpr() is not None:
            return None
        and_ctx = or_ctx.andExpr()
        if and_ctx.andExpr() is not None:
            return None
        cmp_ctx = and_ctx.cmpExpr()
        if cmp_ctx.cmpExpr() is not None:
            return None
        add_ctx = cmp_ctx.addExpr()
        if add_ctx.addExpr() is not None:
            return None
        mul_ctx = add_ctx.mulExpr()
        if mul_ctx.mulExpr() is not None:
            return None
        pow_ctx = mul_ctx.powExpr()
        if pow_ctx.powExpr() is not None:
            return None
        unary_ctx = pow_ctx.unaryExpr()
        if unary_ctx.postfixExpr() is None:
            return None
        return unary_ctx.postfixExpr()

    def _base_ident_of_postfix(self, postfix_ctx):
        while postfix_ctx is not None:
            if postfix_ctx.primary() is not None:
                primary = postfix_ctx.primary()
                if primary.IDENT() is not None and primary.getChild(0).getText() != 'new':
                    return primary.IDENT().getText()
                return None
            postfix_ctx = postfix_ctx.postfixExpr()
        return None

    def _check_lvalue_assignable(self, postfix_ctx):
        if postfix_ctx.argList() is not None:
            self.errors.add_error(
                postfix_ctx.start.line,
                "não é possível atribuir ao resultado de uma chamada"
            )
            return

        if postfix_ctx.expr() is not None:
            base_ident = self._base_ident_of_postfix(postfix_ctx.postfixExpr())
            if base_ident is not None:
                info = self.lookup(base_ident)
                if info is not None and info.get('categoria') == 'const':
                    self.errors.add_error(
                        postfix_ctx.start.line,
                        f"não é possível alterar elemento do vetor constante '{base_ident}'"
                    )
            return

        if postfix_ctx.IDENT() is not None:
            base_ident = self._base_ident_of_postfix(postfix_ctx.postfixExpr())
            if base_ident is not None:
                info = self.lookup(base_ident)
                if info is not None and info.get('categoria') == 'const':
                    self.errors.add_error(
                        postfix_ctx.start.line,
                        f"não é possível alterar atributo do objeto constante '{base_ident}'"
                    )
            return

        if postfix_ctx.primary() is None:
            return
        primary = postfix_ctx.primary()
        if primary.IDENT() is None:
            self.errors.add_error(
                postfix_ctx.start.line,
                "lado esquerdo da atribuição não é um destino válido"
            )
            return
        if primary.getChild(0).getText() == 'new':
            self.errors.add_error(
                postfix_ctx.start.line,
                "não é possível atribuir a uma expressão 'new'"
            )
            return
        ident_tok = primary.IDENT()
        nome = ident_tok.getText()
        info = self.lookup(nome)
        if info is None:
            return
        cat = info.get('categoria')
        if cat == 'const':
            self.errors.add_error(
                ident_tok.symbol.line,
                f"não é possível atribuir à constante '{nome}'"
            )
        elif cat not in ('var', 'param'):
            self.errors.add_error(
                ident_tok.symbol.line,
                f"'{nome}' não é uma variável e não pode receber atribuição"
            )

    # ─── Expressões: cadeia que devolve tipo + valida operadores ─

    def _is_array_literal(self, expr_ctx):
        if expr_ctx.assignOp() is not None:
            return False
        or_ctx = expr_ctx.orExpr()
        if or_ctx.orExpr() is not None: return False
        and_ctx = or_ctx.andExpr()
        if and_ctx.andExpr() is not None: return False
        cmp_ctx = and_ctx.cmpExpr()
        if cmp_ctx.cmpExpr() is not None: return False
        add_ctx = cmp_ctx.addExpr()
        if add_ctx.addExpr() is not None: return False
        mul_ctx = add_ctx.mulExpr()
        if mul_ctx.mulExpr() is not None: return False
        pow_ctx = mul_ctx.powExpr()
        if pow_ctx.powExpr() is not None: return False
        unary_ctx = pow_ctx.unaryExpr()
        if unary_ctx.postfixExpr() is None: return False
        postfix_ctx = unary_ctx.postfixExpr()
        if postfix_ctx.primary() is None: return False
        primary = postfix_ctx.primary()
        return primary.getChildCount() > 0 and primary.getChild(0).getText() == '['

    def visitExpr(self, ctx):
        if ctx.assignOp() is None:
            return self.visit(ctx.orExpr())

        if self._is_array_literal(ctx.expr()):
            self.errors.add_error(
                ctx.start.line,
                "literal de vetor só pode aparecer na inicialização de uma declaração"
            )

        lhs_type = self.visit(ctx.orExpr())
        rhs_type = self.visit(ctx.expr())
        op = ctx.assignOp().getText()
        line = ctx.start.line

        lvalue = self._extract_lvalue(ctx.orExpr())
        if lvalue is None:
            self.errors.add_error(line, f"lado esquerdo de '{op}' não é um destino atribuível")
            return lhs_type

        self._check_lvalue_assignable(lvalue)

        if op == '=':
            if not self._is_assignable(lhs_type, rhs_type):
                self.errors.add_error(
                    line,
                    f"não é possível atribuir '{rhs_type}' a '{lhs_type}'"
                )
        else:
            bin_op = op[:-1]
            if bin_op == '%':
                result = self._check_int_binop(ctx, lhs_type, rhs_type, bin_op)
            else:
                result = self._check_arith_binop(ctx, lhs_type, rhs_type, bin_op)
            if result != '?' and not self._is_assignable(lhs_type, result):
                self.errors.add_error(
                    line,
                    f"não é possível atribuir resultado '{result}' a '{lhs_type}'"
                )

        return lhs_type

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
            if self._class_stack:
                return self._class_stack[-1]
            self.errors.add_error(ctx.start.line, "'this' usado fora de uma classe")
            return '?'

        if first_text == 'new':
            ident_tok = ctx.IDENT()
            nome = ident_tok.getText()
            linha = ident_tok.symbol.line
            info = self.lookup(nome)

            arg_types = []
            if ctx.argList() is not None:
                for e in ctx.argList().expr():
                    arg_types.append(self.visit(e))

            if info is None:
                self.errors.add_error(linha, f"classe '{nome}' não declarada")
                return '?'
            if info.get('categoria') != 'class':
                self.errors.add_error(linha, f"'{nome}' não é uma classe")
                return '?'

            ctor = info.get('constructor')
            if ctor is not None:
                self._check_args(ctx, ctor['params'], arg_types, f"constructor de '{nome}'")
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
            target = ctx.castType().getText()
            arg_type = self.visit(ctx.expr(0))
            if arg_type != '?':
                if target == 'str':
                    if not self._is_primitive(arg_type):
                        self.errors.add_error(
                            ctx.start.line,
                            f"cast 'str()' requer operando primitivo, recebeu '{arg_type}'"
                        )
                else:
                    if arg_type not in ('int', 'real', 'bool'):
                        self.errors.add_error(
                            ctx.start.line,
                            f"cast '{target}()' requer operando numérico ou 'bool', recebeu '{arg_type}'"
                        )
            return target

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
            return self._handle_call(ctx)

        if ctx.IDENT() is not None:
            return self._handle_member_access(ctx)

        if ctx.expr() is not None:
            return self._handle_array_access(ctx)

        return '?'

    def _handle_call(self, ctx):
        callee = ctx.postfixExpr()
        arg_types = []
        if ctx.argList() is not None:
            for e in ctx.argList().expr():
                arg_types.append(self.visit(e))

        if callee.primary() is not None:
            return self._direct_call(callee, ctx, arg_types)

        if callee.IDENT() is not None:
            return self._method_call(callee, ctx, arg_types)

        return '?'

    def _direct_call(self, callee, call_ctx, arg_types):
        primary = callee.primary()
        if primary.IDENT() is None:
            return '?'
        if primary.getChild(0).getText() == 'new':
            return '?'

        ident_tok = primary.IDENT()
        nome = ident_tok.getText()
        linha = ident_tok.symbol.line
        info = self.lookup(nome)
        if info is None:
            self.errors.add_error(linha, f"identificador '{nome}' não declarado")
            return '?'

        cat = info.get('categoria')
        if cat == 'function':
            self._check_args(call_ctx, info.get('params', []), arg_types, f"função '{nome}'")
            return info.get('tipo_retorno', '?')
        if cat == 'builtin_function':
            if nome == 'input':
                self._validate_input_args(call_ctx, arg_types)
            return 'void'
        if cat == 'class':
            self.errors.add_error(
                linha,
                f"para criar um objeto da classe '{nome}', use 'new {nome}(...)'"
            )
            return '?'
        self.errors.add_error(
            linha,
            f"'{nome}' não é uma função e não pode ser chamada"
        )
        return '?'

    def _method_call(self, callee, call_ctx, arg_types):
        member_tok = callee.IDENT()
        member = member_tok.getText()
        line = member_tok.symbol.line
        base = callee.postfixExpr()

        if base.primary() is not None:
            primary = base.primary()
            if primary.IDENT() is not None and primary.getChild(0).getText() != 'new':
                base_info = self.lookup(primary.IDENT().getText())
                if base_info is not None and base_info.get('categoria') == 'builtin_obj':
                    membros = base_info.get('membros', set())
                    if member not in membros:
                        self.errors.add_error(
                            line,
                            f"'{primary.IDENT().getText()}' não possui o membro '{member}'"
                        )
                    elif member == 'log':
                        self._validate_console_log_args(call_ctx, arg_types)
                    return 'void'

        base_type = self.visit(base)

        if base_type == '?':
            return '?'
        if base_type == 'null':
            self.errors.add_error(line, "chamada de método em 'null'")
            return '?'
        if self._is_primitive(base_type) or base_type.endswith('[]'):
            self.errors.add_error(
                line,
                f"chamada '.{member}()' em tipo '{base_type}' (não é objeto)"
            )
            return '?'

        class_info = self.lookup(base_type)
        if class_info is None or class_info.get('categoria') != 'class':
            return '?'

        metodos = class_info.get('metodos', {})
        if member not in metodos:
            atributos = class_info.get('atributos', {})
            if member in atributos:
                self.errors.add_error(
                    line,
                    f"'{member}' é atributo de '{base_type}', não pode ser chamado"
                )
            else:
                self.errors.add_error(
                    line,
                    f"método '{member}' não existe em '{base_type}'"
                )
            return '?'

        method_info = metodos[member]
        self._check_args(
            call_ctx, method_info['params'], arg_types,
            f"método '{base_type}.{member}'"
        )
        return method_info['tipo_retorno']

    def _handle_member_access(self, ctx):
        member_tok = ctx.IDENT()
        member = member_tok.getText()
        line = member_tok.symbol.line
        base = ctx.postfixExpr()

        if base.primary() is not None:
            primary = base.primary()
            if primary.IDENT() is not None and primary.getChild(0).getText() != 'new':
                base_info = self.lookup(primary.IDENT().getText())
                if base_info is not None and base_info.get('categoria') == 'builtin_obj':
                    membros = base_info.get('membros', set())
                    if member not in membros:
                        self.errors.add_error(
                            line,
                            f"'{primary.IDENT().getText()}' não possui o membro '{member}'"
                        )
                    return '?'

        base_type = self.visit(base)

        if base_type == '?':
            return '?'
        if base_type == 'null':
            self.errors.add_error(line, f"acesso '.{member}' em 'null'")
            return '?'
        if self._is_primitive(base_type) or base_type.endswith('[]'):
            self.errors.add_error(
                line,
                f"acesso '.{member}' em tipo '{base_type}' (não é objeto)"
            )
            return '?'

        class_info = self.lookup(base_type)
        if class_info is None or class_info.get('categoria') != 'class':
            return '?'

        atributos = class_info.get('atributos', {})
        if member in atributos:
            return atributos[member]
        if member in class_info.get('metodos', {}):
            return '?'

        self.errors.add_error(line, f"'{base_type}' não possui membro '{member}'")
        return '?'

    def _handle_array_access(self, ctx):
        base_type = self.visit(ctx.postfixExpr())
        index_type = self.visit(ctx.expr())
        linha = ctx.expr().start.line

        if base_type != '?' and not base_type.endswith('[]'):
            self.errors.add_error(
                linha,
                f"acesso com '[]' em valor não-vetor (tipo '{base_type}')"
            )
            return '?'

        if index_type not in ('int', '?'):
            self.errors.add_error(
                linha,
                f"índice de vetor deve ser 'int', recebeu '{index_type}'"
            )

        if base_type and base_type.endswith('[]'):
            return base_type[:-2]
        return '?'
