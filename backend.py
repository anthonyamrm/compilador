import ctypes
import os
import shutil
import subprocess
import tempfile

from llvmlite import ir, binding

from JSSVisitor import JSSVisitor
from JSSParser import JSSParser

binding.initialize_native_target()
binding.initialize_native_asmprinter()


class CodegenError(Exception):
    pass


I32 = ir.IntType(32)
I64 = ir.IntType(64)
I8 = ir.IntType(8)
I1 = ir.IntType(1)
F64 = ir.DoubleType()
VOID = ir.VoidType()
I8P = I8.as_pointer()


class LLVMCodeGenerator(JSSVisitor):
    """Gera LLVM IR para uma árvore JSS já validada pelo SemanticAnalyzer.

    Estrutura de escopos/percurso espelha semantic_analyzer.py, mas cada
    visitXxx de expressão retorna (llvm_value, jss_type) e emite instruções
    via llvmlite.ir.IRBuilder em vez de só inferir tipos.
    """

    def __init__(self, module_name='jss_module'):
        super().__init__()
        self.module = ir.Module(name=module_name)
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        self.module.triple = target.triple
        self.module.data_layout = str(target_machine.target_data)

        self.scopes = [{}]
        self.builder = None
        self._break_targets = []
        self._function_stack = []
        self._this_stack = []
        self._str_cache = {}
        self._str_counter = 0

        self._register_builtins()
        self._declare_externs()
        self._declare_helpers()

    #  Pilha de escopos 

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def current_scope(self):
        return self.scopes[-1]

    def declare(self, name, info):
        self.current_scope()[name] = info

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def _register_builtins(self):
        self.scopes[0]['input'] = {'categoria': 'builtin_function'}
        self.scopes[0]['console'] = {'categoria': 'builtin_obj', 'membros': {'log'}}

    # ─── Runtime externo ───────────────────────────────────────────

    def _declare_externs(self):
        self.printf_fn = ir.Function(
            self.module, ir.FunctionType(I32, [I8P], var_arg=True), name='printf')
        self.scanf_fn = ir.Function(
            self.module, ir.FunctionType(I32, [I8P], var_arg=True), name='scanf')
        self.malloc_fn = ir.Function(
            self.module, ir.FunctionType(I8P, [I64]), name='malloc')
        self.sprintf_fn = ir.Function(
            self.module, ir.FunctionType(I32, [I8P, I8P], var_arg=True), name='sprintf')
        self.strlen_fn = ir.Function(
            self.module, ir.FunctionType(I64, [I8P]), name='strlen')
        self.strcpy_fn = ir.Function(
            self.module, ir.FunctionType(I8P, [I8P, I8P]), name='strcpy')
        self.strcat_fn = ir.Function(
            self.module, ir.FunctionType(I8P, [I8P, I8P]), name='strcat')
        self.strcmp_fn = ir.Function(
            self.module, ir.FunctionType(I32, [I8P, I8P]), name='strcmp')

    def _declare_helpers(self):
        # jss_str_concat(i8*, i8*) -> i8*
        fn = ir.Function(
            self.module, ir.FunctionType(I8P, [I8P, I8P]), name='jss_str_concat')
        a, b = fn.args
        bb = fn.append_basic_block('entry')
        bld = ir.IRBuilder(bb)
        la = bld.call(self.strlen_fn, [a])
        lb = bld.call(self.strlen_fn, [b])
        total = bld.add(bld.add(la, lb), ir.Constant(I64, 1))
        buf = bld.call(self.malloc_fn, [total])
        bld.call(self.strcpy_fn, [buf, a])
        bld.call(self.strcat_fn, [buf, b])
        bld.ret(buf)
        self.str_concat_fn = fn

        # jss_ipow(i32, i32) -> i32  (expoente inteiro não-negativo)
        fn2 = ir.Function(
            self.module, ir.FunctionType(I32, [I32, I32]), name='jss_ipow')
        base, exp = fn2.args
        entry = fn2.append_basic_block('entry')
        loop_bb = fn2.append_basic_block('loop')
        body_bb = fn2.append_basic_block('body')
        end_bb = fn2.append_basic_block('end')
        b2 = ir.IRBuilder(entry)
        result_ptr = b2.alloca(I32, name='result')
        b2.store(ir.Constant(I32, 1), result_ptr)
        i_ptr = b2.alloca(I32, name='i')
        b2.store(ir.Constant(I32, 0), i_ptr)
        b2.branch(loop_bb)

        b2.position_at_end(loop_bb)
        i_val = b2.load(i_ptr)
        cond = b2.icmp_signed('<', i_val, exp)
        b2.cbranch(cond, body_bb, end_bb)

        b2.position_at_end(body_bb)
        cur = b2.load(result_ptr)
        b2.store(b2.mul(cur, base), result_ptr)
        b2.store(b2.add(i_val, ir.Constant(I32, 1)), i_ptr)
        b2.branch(loop_bb)

        b2.position_at_end(end_bb)
        b2.ret(b2.load(result_ptr))
        self.ipow_fn = fn2

    # ─── Tipos: JSS -> LLVM ─────────────────────────────────────────

    def llvm_type_for(self, jss_type):
        base = {
            'int': I32, 'real': F64, 'bool': I8, 'str': I8P,
            'void': VOID, 'null': I8P,
        }.get(jss_type)
        if base is not None:
            return base
        if jss_type.endswith('[]'):
            return self.llvm_type_for(jss_type[:-2]).as_pointer()
        info = self.lookup(jss_type)
        if info is not None and info.get('categoria') == 'class':
            return info['struct'].as_pointer()
        raise CodegenError(f"tipo desconhecido: {jss_type}")

    def _build_type(self, type_ctx, dims):
        return type_ctx.getText() + '[]' * len(dims)

    def _dims_values(self, dims):
        return [int(d.getText()) for d in dims]

    # ─── Helpers de memória ────────────────────────────────────────

    def _sizeof(self, llvm_type, builder):
        ptr_ty = llvm_type.as_pointer()
        null = ir.Constant(ptr_ty, None)
        gep = builder.gep(null, [ir.Constant(I32, 1)])
        return builder.ptrtoint(gep, I64)

    def _malloc_n(self, elem_llvm_type, count_i64, builder):
        elem_size = self._sizeof(elem_llvm_type, builder)
        total = builder.mul(elem_size, count_i64)
        raw = builder.call(self.malloc_fn, [total])
        return builder.bitcast(raw, elem_llvm_type.as_pointer())

    def _alloc_array(self, dims, base_type, builder):
        d0 = dims[0]
        rest = dims[1:]
        elem_type_str = base_type + '[]' * len(rest)
        elem_llvm_type = self.llvm_type_for(elem_type_str)
        arr_ptr = self._malloc_n(elem_llvm_type, ir.Constant(I64, d0), builder)
        if rest:
            for i in range(d0):
                row = self._alloc_array(rest, base_type, builder)
                slot = builder.gep(arr_ptr, [ir.Constant(I32, i)])
                builder.store(row, slot)
        return arr_ptr

    def _global_str_ptr(self, text):
        cached = self._str_cache.get(text)
        if cached is not None:
            return cached
        data = bytearray(text.encode('utf-8')) + b'\x00'
        arr_ty = ir.ArrayType(I8, len(data))
        name = f'.str.{self._str_counter}'
        self._str_counter += 1
        g = ir.GlobalVariable(self.module, arr_ty, name=name)
        g.global_constant = True
        g.linkage = 'internal'
        g.initializer = ir.Constant(arr_ty, data)
        ptr = g.gep([ir.Constant(I32, 0), ir.Constant(I32, 0)])
        self._str_cache[text] = ptr
        return ptr

    def _unescape(self, raw_text):
        inner = raw_text[1:-1]
        escapes = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\', '0': '\0'}
        out = []
        i = 0
        while i < len(inner):
            c = inner[i]
            if c == '\\' and i + 1 < len(inner):
                out.append(escapes.get(inner[i + 1], inner[i + 1]))
                i += 2
            else:
                out.append(c)
                i += 1
        return ''.join(out)

    def _to_i1(self, i8val):
        return self.builder.icmp_unsigned('!=', i8val, ir.Constant(I8, 0))

    # ─── Coerção de tipos (promoção int->real, null->ponteiro) ───

    def _coerce(self, val, from_type, to_type):
        if from_type == to_type:
            return val
        if to_type == 'real' and from_type == 'int':
            return self.builder.sitofp(val, F64)
        if from_type == 'null':
            return ir.Constant(self.llvm_type_for(to_type), None)
        return val

    #  Ponto de entrada 

    def generate(self, tree):
        self._pass1(tree)
        self._pass2(tree)
        return self.module

    def _pass1(self, tree):
        for top in tree.topDecl():
            if top.classDecl() is not None:
                self._declare_class_stub(top.classDecl())
        for top in tree.topDecl():
            if top.classDecl() is not None:
                self._declare_class_members(top.classDecl())
        for top in tree.topDecl():
            if top.functionDecl() is not None:
                self._declare_function_proto(top.functionDecl())
            elif top.statement() is not None:
                stmt = top.statement()
                if stmt.varDecl() is not None:
                    self._declare_global_var(stmt.varDecl())
                elif stmt.constDecl() is not None:
                    self._declare_global_const(stmt.constDecl())

    def _pass2(self, tree):
        for top in tree.topDecl():
            if top.functionDecl() is not None:
                self._generate_function_body(top.functionDecl())
            elif top.classDecl() is not None:
                self._generate_class_bodies(top.classDecl())
        self._generate_main(tree)

    #  declarações 

    def _declare_class_stub(self, ctx):
        nome = ctx.IDENT().getText()
        struct = self.module.context.get_identified_type(nome)
        self.declare(nome, {
            'categoria': 'class', 'struct': struct,
            'atributos': {}, 'attr_order': [], 'metodos': {}, 'constructor': None,
        })

    def _declare_class_members(self, ctx):
        nome = ctx.IDENT().getText()
        info = self.lookup(nome)
        struct = info['struct']

        atributos = {}
        attr_order = []
        attr_types = []
        idx = 0
        for member in ctx.classMember():
            if member.attrDecl() is not None:
                a = member.attrDecl()
                a_nome = a.IDENT().getText()
                a_tipo = self._build_type(a.type_(), a.INT_LIT())
                a_dims = self._dims_values(a.INT_LIT())
                a_base = a.type_().getText()
                atributos[a_nome] = (idx, a_tipo, a_dims, a_base)
                attr_order.append(a_nome)
                attr_types.append(self.llvm_type_for(a_tipo))
                idx += 1
        struct.set_body(*attr_types)
        info['atributos'] = atributos
        info['attr_order'] = attr_order

        this_ptr_ty = struct.as_pointer()
        metodos = {}
        constructor = None
        for member in ctx.classMember():
            if member.constructorDecl() is not None:
                c = member.constructorDecl()
                param_types = []
                if c.params() is not None:
                    for p in c.params().param():
                        param_types.append(self._build_type(p.type_(), p.INT_LIT()))
                llvm_params = [this_ptr_ty] + [self.llvm_type_for(t) for t in param_types]
                llvm_func = ir.Function(
                    self.module, ir.FunctionType(VOID, llvm_params),
                    name=f'{nome}__constructor')
                constructor = {'params': param_types, 'llvm_func': llvm_func}
            elif member.methodDecl() is not None:
                m = member.methodDecl()
                m_nome = m.IDENT().getText()
                m_tipo = self._build_type(m.type_(), m.INT_LIT())
                param_types = []
                if m.params() is not None:
                    for p in m.params().param():
                        param_types.append(self._build_type(p.type_(), p.INT_LIT()))
                llvm_params = [this_ptr_ty] + [self.llvm_type_for(t) for t in param_types]
                llvm_func = ir.Function(
                    self.module, ir.FunctionType(self.llvm_type_for(m_tipo), llvm_params),
                    name=f'{nome}__{m_nome}')
                metodos[m_nome] = {
                    'tipo_retorno': m_tipo, 'params': param_types, 'llvm_func': llvm_func,
                }
        info['metodos'] = metodos
        info['constructor'] = constructor

    def _declare_function_proto(self, ctx):
        nome = ctx.IDENT().getText()
        tipo_retorno = self._build_type(ctx.type_(), ctx.INT_LIT())
        param_types = []
        if ctx.params() is not None:
            for p in ctx.params().param():
                param_types.append(self._build_type(p.type_(), p.INT_LIT()))
        llvm_ret = self.llvm_type_for(tipo_retorno)
        llvm_params = [self.llvm_type_for(t) for t in param_types]
        llvm_func = ir.Function(
            self.module, ir.FunctionType(llvm_ret, llvm_params), name=f'jss_{nome}')
        self.declare(nome, {
            'categoria': 'function', 'tipo_retorno': tipo_retorno,
            'params': param_types, 'llvm_func': llvm_func,
        })

    def _declare_global_var(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        llvm_ty = self.llvm_type_for(tipo)
        for d in ctx.declarator():
            nome = d.IDENT().getText()
            g = ir.GlobalVariable(self.module, llvm_ty, name=f'g_{nome}')
            g.initializer = ir.Constant(llvm_ty, None)
            g.linkage = 'internal'
            self.declare(nome, {'categoria': 'var', 'tipo': tipo, 'ptr': g})

    def _declare_global_const(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        llvm_ty = self.llvm_type_for(tipo)
        nome = ctx.IDENT().getText()
        g = ir.GlobalVariable(self.module, llvm_ty, name=f'g_{nome}')
        g.initializer = ir.Constant(llvm_ty, None)
        g.linkage = 'internal'
        self.declare(nome, {'categoria': 'const', 'tipo': tipo, 'ptr': g})

    # ─── Fase 2: corpos ─────────────────────────────────────────────

    def _generate_callable_body(self, params_ctx, block_ctx, llvm_func, tipo_retorno,
                                 kind, this_class=None):
        entry = llvm_func.append_basic_block('entry')
        self.builder = ir.IRBuilder(entry)
        self.push_scope()
        self._function_stack.append(
            {'llvm_func': llvm_func, 'tipo_retorno': tipo_retorno, 'kind': kind})

        arg_iter = iter(llvm_func.args)
        if this_class is not None:
            self._this_stack.append((next(arg_iter), this_class))

        if params_ctx is not None:
            for p, arg in zip(params_ctx.param(), arg_iter):
                p_nome = p.IDENT().getText()
                p_tipo = self._build_type(p.type_(), p.INT_LIT())
                ptr = self.builder.alloca(self.llvm_type_for(p_tipo), name=p_nome)
                self.builder.store(arg, ptr)
                self.declare(p_nome, {'categoria': 'param', 'tipo': p_tipo, 'ptr': ptr})

        self.visit(block_ctx)

        if not self.builder.block.is_terminated:
            if tipo_retorno == 'void':
                self.builder.ret_void()
            else:
                self.builder.unreachable()

        self.pop_scope()
        self._function_stack.pop()
        if this_class is not None:
            self._this_stack.pop()

    def _generate_function_body(self, ctx):
        nome = ctx.IDENT().getText()
        info = self.lookup(nome)
        self._generate_callable_body(
            ctx.params(), ctx.block(), info['llvm_func'], info['tipo_retorno'], 'function')

    def _generate_class_bodies(self, ctx):
        nome = ctx.IDENT().getText()
        info = self.lookup(nome)
        for member in ctx.classMember():
            if member.constructorDecl() is not None:
                c = member.constructorDecl()
                ctor = info['constructor']
                self._generate_callable_body(
                    c.params(), c.block(), ctor['llvm_func'], 'void', 'constructor',
                    this_class=nome)
            elif member.methodDecl() is not None:
                m = member.methodDecl()
                m_nome = m.IDENT().getText()
                minfo = info['metodos'][m_nome]
                self._generate_callable_body(
                    m.params(), m.block(), minfo['llvm_func'], minfo['tipo_retorno'],
                    'method', this_class=nome)

    def _generate_main(self, tree):
        main_ty = ir.FunctionType(I32, [])
        main_fn = ir.Function(self.module, main_ty, name='main')
        entry = main_fn.append_basic_block('entry')
        self.builder = ir.IRBuilder(entry)
        self._function_stack.append(
            {'llvm_func': main_fn, 'tipo_retorno': 'void', 'kind': 'script'})
        self._break_targets = []

        for top in tree.topDecl():
            stmt = top.statement()
            if stmt is None:
                continue
            if self.builder.block.is_terminated:
                break
            if stmt.varDecl() is not None:
                self._init_global_vardecl(stmt.varDecl())
            elif stmt.constDecl() is not None:
                self._init_global_constdecl(stmt.constDecl())
            else:
                self.visit(stmt)

        user_main = self.lookup('main')
        if (not self.builder.block.is_terminated and user_main is not None
                and user_main.get('categoria') == 'function'):
            self.builder.call(user_main['llvm_func'], [])

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(I32, 0))

        self._function_stack.pop()

    def _init_global_vardecl(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        base_type = ctx.type_().getText()
        dims = self._dims_values(ctx.INT_LIT())
        for d in ctx.declarator():
            nome = d.IDENT().getText()
            ptr = self.lookup(nome)['ptr']
            if d.expr() is not None:
                val, vtype = self.visit(d.expr())
                self.builder.store(self._coerce(val, vtype, tipo), ptr)
            elif dims:
                self.builder.store(self._alloc_array(dims, base_type, self.builder), ptr)

    def _init_global_constdecl(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        nome = ctx.IDENT().getText()
        ptr = self.lookup(nome)['ptr']
        val, vtype = self.visit(ctx.expr())
        self.builder.store(self._coerce(val, vtype, tipo), ptr)

    # ─── Statements ─────────────────────────────────────────────────

    def visitBlock(self, ctx):
        self.push_scope()
        for stmt in ctx.statement():
            if self.builder.block.is_terminated:
                break
            self.visit(stmt)
        self.pop_scope()
        return None

    def visitVarDecl(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        base_type = ctx.type_().getText()
        dims = self._dims_values(ctx.INT_LIT())
        llvm_ty = self.llvm_type_for(tipo)
        for d in ctx.declarator():
            nome = d.IDENT().getText()
            ptr = self.builder.alloca(llvm_ty, name=nome)
            self.builder.store(ir.Constant(llvm_ty, None), ptr)
            self.declare(nome, {'categoria': 'var', 'tipo': tipo, 'ptr': ptr})
            if d.expr() is not None:
                val, vtype = self.visit(d.expr())
                self.builder.store(self._coerce(val, vtype, tipo), ptr)
            elif dims:
                self.builder.store(self._alloc_array(dims, base_type, self.builder), ptr)
        return None

    def visitVarDeclNoSemi(self, ctx):
        return self.visitVarDecl(ctx)

    def visitConstDecl(self, ctx):
        tipo = self._build_type(ctx.type_(), ctx.INT_LIT())
        llvm_ty = self.llvm_type_for(tipo)
        nome = ctx.IDENT().getText()
        ptr = self.builder.alloca(llvm_ty, name=nome)
        self.declare(nome, {'categoria': 'const', 'tipo': tipo, 'ptr': ptr})
        val, vtype = self.visit(ctx.expr())
        self.builder.store(self._coerce(val, vtype, tipo), ptr)
        return None

    def visitReturnStmt(self, ctx):
        if ctx.expr() is not None:
            val, vtype = self.visit(ctx.expr())
            declared = self._function_stack[-1]['tipo_retorno']
            self.builder.ret(self._coerce(val, vtype, declared))
        else:
            self.builder.ret_void()
        return None

    def visitIfStmt(self, ctx):
        cond_val, _ = self.visit(ctx.expr())
        cond_i1 = self._to_i1(cond_val)
        then_bb = self.builder.append_basic_block('if.then')
        else_bb = self.builder.append_basic_block('if.else') if ctx.elseClause() is not None else None
        merge_bb = self.builder.append_basic_block('if.end')

        self.builder.cbranch(cond_i1, then_bb, else_bb if else_bb is not None else merge_bb)

        self.builder.position_at_end(then_bb)
        self.visit(ctx.block())
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        if else_bb is not None:
            self.builder.position_at_end(else_bb)
            self.visit(ctx.elseClause())
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        self.builder.position_at_end(merge_bb)
        return None

    def visitElseClause(self, ctx):
        if ctx.ifStmt() is not None:
            return self.visit(ctx.ifStmt())
        return self.visit(ctx.block())

    def visitWhileStmt(self, ctx):
        cond_bb = self.builder.append_basic_block('while.cond')
        body_bb = self.builder.append_basic_block('while.body')
        end_bb = self.builder.append_basic_block('while.end')

        self.builder.branch(cond_bb)
        self.builder.position_at_end(cond_bb)
        cond_val, _ = self.visit(ctx.expr())
        self.builder.cbranch(self._to_i1(cond_val), body_bb, end_bb)

        self.builder.position_at_end(body_bb)
        self._break_targets.append(end_bb)
        self.visit(ctx.block())
        self._break_targets.pop()
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)

        self.builder.position_at_end(end_bb)
        return None

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

    def visitForStmt(self, ctx):
        self.push_scope()
        if ctx.forInit() is not None:
            self.visit(ctx.forInit())

        cond_ctx, update_ctx = self._for_parts(ctx)

        cond_bb = self.builder.append_basic_block('for.cond')
        body_bb = self.builder.append_basic_block('for.body')
        update_bb = self.builder.append_basic_block('for.update')
        end_bb = self.builder.append_basic_block('for.end')

        self.builder.branch(cond_bb)
        self.builder.position_at_end(cond_bb)
        if cond_ctx is not None:
            cond_val, _ = self.visit(cond_ctx)
            self.builder.cbranch(self._to_i1(cond_val), body_bb, end_bb)
        else:
            self.builder.branch(body_bb)

        self.builder.position_at_end(body_bb)
        self._break_targets.append(end_bb)
        self.visit(ctx.block())
        self._break_targets.pop()
        if not self.builder.block.is_terminated:
            self.builder.branch(update_bb)

        self.builder.position_at_end(update_bb)
        if update_ctx is not None:
            self.visit(update_ctx)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)

        self.builder.position_at_end(end_bb)
        self.pop_scope()
        return None

    def visitForInit(self, ctx):
        if ctx.varDeclNoSemi() is not None:
            return self.visit(ctx.varDeclNoSemi())
        return self.visit(ctx.expr())

    def visitBreakStmt(self, ctx):
        if self._break_targets:
            self.builder.branch(self._break_targets[-1])
        return None

    def visitExprStmt(self, ctx):
        self.visit(ctx.expr())
        return None

    # ─── Expressões: lvalues ────────────────────────────────────────

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

    def _extract_lvalue_from_expr(self, expr_ctx):
        if expr_ctx.assignOp() is not None:
            return None
        return self._extract_lvalue(expr_ctx.orExpr())

    def _resolve_lvalue_ptr(self, postfix_ctx):
        if postfix_ctx.expr() is not None:
            base_val, base_type = self.visit(postfix_ctx.postfixExpr())
            idx_val, _ = self.visit(postfix_ctx.expr())
            elem_type = base_type[:-2]
            elem_ptr = self.builder.gep(base_val, [idx_val])
            return elem_ptr, elem_type

        if postfix_ctx.IDENT() is not None:
            base_val, base_type = self.visit(postfix_ctx.postfixExpr())
            member = postfix_ctx.IDENT().getText()
            class_info = self.lookup(base_type)
            idx, attr_type = class_info['atributos'][member][:2]
            field_ptr = self.builder.gep(
                base_val, [ir.Constant(I32, 0), ir.Constant(I32, idx)], inbounds=True)
            return field_ptr, attr_type

        primary = postfix_ctx.primary()
        nome = primary.IDENT().getText()
        info = self.lookup(nome)
        return info['ptr'], info['tipo']

    # ─── Expressões: atribuição ─────────────────────────────────────

    def visitExpr(self, ctx):
        if ctx.assignOp() is None:
            return self.visit(ctx.orExpr())

        lvalue_postfix = self._extract_lvalue(ctx.orExpr())
        ptr, target_type = self._resolve_lvalue_ptr(lvalue_postfix)
        op = ctx.assignOp().getText()
        rhs_val, rhs_type = self.visit(ctx.expr())

        if op == '=':
            val = self._coerce(rhs_val, rhs_type, target_type)
            self.builder.store(val, ptr)
            return val, target_type

        bin_op = op[:-1]
        cur = self.builder.load(ptr)
        if bin_op == '%':
            result_val, result_type = self.builder.srem(cur, rhs_val), 'int'
        else:
            result_val, result_type = self._arith(bin_op, cur, target_type, rhs_val, rhs_type)
        val = self._coerce(result_val, result_type, target_type)
        self.builder.store(val, ptr)
        return val, target_type

    # ─── Expressões: lógicos (curto-circuito) ────────────────────────

    def visitOrExpr(self, ctx):
        if ctx.orExpr() is None:
            return self.visit(ctx.andExpr())
        left_val, _ = self.visit(ctx.orExpr())
        left_i1 = self._to_i1(left_val)
        cur_bb = self.builder.block
        rhs_bb = self.builder.append_basic_block('or.rhs')
        merge_bb = self.builder.append_basic_block('or.merge')
        self.builder.cbranch(left_i1, merge_bb, rhs_bb)

        self.builder.position_at_end(rhs_bb)
        right_val, _ = self.visit(ctx.andExpr())
        rhs_end_bb = self.builder.block
        self.builder.branch(merge_bb)

        self.builder.position_at_end(merge_bb)
        phi = self.builder.phi(I8)
        phi.add_incoming(ir.Constant(I8, 1), cur_bb)
        phi.add_incoming(right_val, rhs_end_bb)
        return phi, 'bool'

    def visitAndExpr(self, ctx):
        if ctx.andExpr() is None:
            return self.visit(ctx.cmpExpr())
        left_val, _ = self.visit(ctx.andExpr())
        left_i1 = self._to_i1(left_val)
        cur_bb = self.builder.block
        rhs_bb = self.builder.append_basic_block('and.rhs')
        merge_bb = self.builder.append_basic_block('and.merge')
        self.builder.cbranch(left_i1, rhs_bb, merge_bb)

        self.builder.position_at_end(rhs_bb)
        right_val, _ = self.visit(ctx.cmpExpr())
        rhs_end_bb = self.builder.block
        self.builder.branch(merge_bb)

        self.builder.position_at_end(merge_bb)
        phi = self.builder.phi(I8)
        phi.add_incoming(ir.Constant(I8, 0), cur_bb)
        phi.add_incoming(right_val, rhs_end_bb)
        return phi, 'bool'

    # ─── Expressões: comparação / aritmética ─────────────────────────

    def visitCmpExpr(self, ctx):
        if ctx.cmpExpr() is None:
            return self.visit(ctx.addExpr())
        left_val, left_type = self.visit(ctx.cmpExpr())
        right_val, right_type = self.visit(ctx.addExpr())
        op = ctx.cmpOp().getText()
        if op in ('==', '!='):
            return self._eq(op, left_val, left_type, right_val, right_type)
        return self._rel(op, left_val, left_type, right_val, right_type)

    def _promote(self, lval, ltype, rval, rtype):
        if ltype == 'real' or rtype == 'real':
            if ltype == 'int':
                lval = self.builder.sitofp(lval, F64)
            if rtype == 'int':
                rval = self.builder.sitofp(rval, F64)
            return lval, rval, 'real'
        return lval, rval, 'int'

    def _rel(self, op, lval, ltype, rval, rtype):
        if ltype == 'str' and rtype == 'str':
            cmp = self.builder.call(self.strcmp_fn, [lval, rval])
            result = self.builder.icmp_signed(op, cmp, ir.Constant(I32, 0))
            return self.builder.zext(result, I8), 'bool'
        lval2, rval2, rtype_out = self._promote(lval, ltype, rval, rtype)
        if rtype_out == 'real':
            result = self.builder.fcmp_ordered(op, lval2, rval2)
        else:
            result = self.builder.icmp_signed(op, lval2, rval2)
        return self.builder.zext(result, I8), 'bool'

    def _eq(self, op, lval, ltype, rval, rtype):
        if ltype == 'str' and rtype == 'str':
            cmp = self.builder.call(self.strcmp_fn, [lval, rval])
            result = self.builder.icmp_signed(op, cmp, ir.Constant(I32, 0))
            return self.builder.zext(result, I8), 'bool'
        if ltype == 'null' or rtype == 'null':
            other_val, other_type = (rval, rtype) if ltype == 'null' else (lval, ltype)
            target_ty = self.llvm_type_for(other_type)
            if isinstance(target_ty, ir.PointerType):
                result = self.builder.icmp_unsigned(op, other_val, ir.Constant(target_ty, None))
                return self.builder.zext(result, I8), 'bool'
            return ir.Constant(I8, 1 if op == '!=' else 0), 'bool'
        lval2, rval2, rtype_out = self._promote(lval, ltype, rval, rtype)
        if rtype_out == 'real':
            pred = 'oeq' if op == '==' else 'one'
            result = self.builder.fcmp_ordered(pred, lval2, rval2)
        else:
            result = self.builder.icmp_signed(op, lval2, rval2)
        return self.builder.zext(result, I8), 'bool'

    def visitAddExpr(self, ctx):
        if ctx.addExpr() is None:
            return self.visit(ctx.mulExpr())
        left_val, left_type = self.visit(ctx.addExpr())
        right_val, right_type = self.visit(ctx.mulExpr())
        op = ctx.getChild(1).getText()
        return self._arith(op, left_val, left_type, right_val, right_type)

    def visitMulExpr(self, ctx):
        if ctx.mulExpr() is None:
            return self.visit(ctx.powExpr())
        left_val, left_type = self.visit(ctx.mulExpr())
        right_val, right_type = self.visit(ctx.powExpr())
        op = ctx.getChild(1).getText()
        if op == '%':
            return self.builder.srem(left_val, right_val), 'int'
        return self._arith(op, left_val, left_type, right_val, right_type)

    def visitPowExpr(self, ctx):
        if ctx.powExpr() is None:
            return self.visit(ctx.unaryExpr())
        left_val, _ = self.visit(ctx.unaryExpr())
        right_val, _ = self.visit(ctx.powExpr())
        return self.builder.call(self.ipow_fn, [left_val, right_val]), 'int'

    def _arith(self, op, lval, ltype, rval, rtype):
        if op == '+' and (ltype == 'str' or rtype == 'str'):
            return self.builder.call(self.str_concat_fn, [lval, rval]), 'str'
        lval2, rval2, rtype_out = self._promote(lval, ltype, rval, rtype)
        if rtype_out == 'real':
            fn = {'+': self.builder.fadd, '-': self.builder.fsub,
                  '*': self.builder.fmul, '/': self.builder.fdiv}[op]
            return fn(lval2, rval2), 'real'
        fn = {'+': self.builder.add, '-': self.builder.sub,
              '*': self.builder.mul, '/': self.builder.sdiv}[op]
        return fn(lval2, rval2), 'int'

    # ─── Expressões: unários ──────────────────────────────────────────

    def visitUnaryExpr(self, ctx):
        if ctx.postfixExpr() is not None:
            return self.visit(ctx.postfixExpr())

        op = ctx.getChild(0).getText()

        if op in ('++', '--'):
            inner = ctx.unaryExpr()
            postfix = inner.postfixExpr()
            if postfix is None:
                val, typ = self.visit(inner)
                one = ir.Constant(F64, 1.0) if typ == 'real' else ir.Constant(I32, 1)
                if typ == 'real':
                    return (self.builder.fadd(val, one) if op == '++'
                            else self.builder.fsub(val, one)), typ
                return (self.builder.add(val, one) if op == '++'
                        else self.builder.sub(val, one)), typ
            ptr, typ = self._resolve_lvalue_ptr(postfix)
            cur = self.builder.load(ptr)
            one = ir.Constant(F64, 1.0) if typ == 'real' else ir.Constant(I32, 1)
            if typ == 'real':
                newval = self.builder.fadd(cur, one) if op == '++' else self.builder.fsub(cur, one)
            else:
                newval = self.builder.add(cur, one) if op == '++' else self.builder.sub(cur, one)
            self.builder.store(newval, ptr)
            return newval, typ

        val, typ = self.visit(ctx.unaryExpr())
        if op == '!':
            notv = self.builder.not_(self._to_i1(val))
            return self.builder.zext(notv, I8), 'bool'
        if op == '-':
            return (self.builder.fneg(val) if typ == 'real' else self.builder.neg(val)), typ
        return val, typ

    # ─── Expressões: postfix (chamadas, índice, membro) ───────────────

    def visitPostfixExpr(self, ctx):
        if ctx.primary() is not None:
            return self.visit(ctx.primary())
        if ctx.argList() is not None:
            return self._handle_call(ctx)
        if ctx.IDENT() is not None:
            return self._handle_member_access(ctx)
        if ctx.expr() is not None:
            return self._handle_array_access(ctx)
        raise CodegenError('postfixExpr inesperado')

    def _handle_array_access(self, ctx):
        base_val, base_type = self.visit(ctx.postfixExpr())
        idx_val, _ = self.visit(ctx.expr())
        elem_type = base_type[:-2]
        elem_ptr = self.builder.gep(base_val, [idx_val])
        return self.builder.load(elem_ptr), elem_type

    def _handle_member_access(self, ctx):
        member = ctx.IDENT().getText()
        base = ctx.postfixExpr()

        if base.primary() is not None:
            primary = base.primary()
            if primary.IDENT() is not None and primary.getChild(0).getText() != 'new':
                base_info = self.lookup(primary.IDENT().getText())
                if base_info is not None and base_info.get('categoria') == 'builtin_obj':
                    return ir.Constant(I32, 0), 'void'

        base_val, base_type = self.visit(base)
        class_info = self.lookup(base_type)
        idx, attr_type = class_info['atributos'][member][:2]
        field_ptr = self.builder.gep(
            base_val, [ir.Constant(I32, 0), ir.Constant(I32, idx)], inbounds=True)
        return self.builder.load(field_ptr), attr_type

    def _handle_call(self, ctx):
        callee = ctx.postfixExpr()
        if callee.primary() is not None:
            return self._direct_call(callee, ctx)
        if callee.IDENT() is not None:
            return self._method_call(callee, ctx)
        raise CodegenError('alvo de chamada não suportado')

    def _direct_call(self, callee, call_ctx):
        primary = callee.primary()
        nome = primary.IDENT().getText()
        info = self.lookup(nome)
        cat = info.get('categoria')

        if cat == 'builtin_function':
            self._codegen_input(call_ctx)
            return ir.Constant(I32, 0), 'void'

        arg_vals = []
        if call_ctx.argList() is not None:
            for e in call_ctx.argList().expr():
                arg_vals.append(self.visit(e))

        if cat == 'function':
            coerced = [self._coerce(v, t, pt) for (v, t), pt in zip(arg_vals, info['params'])]
            result = self.builder.call(info['llvm_func'], coerced)
            return result, info['tipo_retorno']

        raise CodegenError(f"não é possível chamar '{nome}'")

    def _method_call(self, callee, call_ctx):
        member = callee.IDENT().getText()
        base = callee.postfixExpr()

        if base.primary() is not None:
            primary = base.primary()
            if primary.IDENT() is not None and primary.getChild(0).getText() != 'new':
                base_info = self.lookup(primary.IDENT().getText())
                if base_info is not None and base_info.get('categoria') == 'builtin_obj':
                    arg_vals = []
                    if call_ctx.argList() is not None:
                        for e in call_ctx.argList().expr():
                            arg_vals.append(self.visit(e))
                    self._codegen_console_log(arg_vals)
                    return ir.Constant(I32, 0), 'void'

        base_val, base_type = self.visit(base)
        class_info = self.lookup(base_type)
        method_info = class_info['metodos'][member]

        arg_vals = []
        if call_ctx.argList() is not None:
            for e in call_ctx.argList().expr():
                arg_vals.append(self.visit(e))

        coerced = [self._coerce(v, t, pt) for (v, t), pt in zip(arg_vals, method_info['params'])]
        result = self.builder.call(method_info['llvm_func'], [base_val] + coerced)
        return result, method_info['tipo_retorno']

    # ─── console.log / input ────────────────────────────────────────

    def _codegen_console_log(self, arg_vals):
        parts_fmt = []
        call_args = []
        for i, (val, typ) in enumerate(arg_vals):
            if i > 0:
                parts_fmt.append(' ')
            if typ == 'int':
                parts_fmt.append('%d')
                call_args.append(val)
            elif typ == 'real':
                parts_fmt.append('%g')
                call_args.append(val)
            elif typ == 'str':
                parts_fmt.append('%s')
                call_args.append(val)
            elif typ == 'bool':
                parts_fmt.append('%s')
                call_args.append(self._to_str(val, 'bool'))
            else:
                parts_fmt.append('%s')
                call_args.append(self._global_str_ptr('?'))
        parts_fmt.append('\n')
        fmt_ptr = self._global_str_ptr(''.join(parts_fmt))
        self.builder.call(self.printf_fn, [fmt_ptr] + call_args)

    def _codegen_input(self, call_ctx):
        if call_ctx.argList() is None:
            return
        for e in call_ctx.argList().expr():
            postfix = self._extract_lvalue_from_expr(e)
            ptr, typ = self._resolve_lvalue_ptr(postfix)
            if typ == 'int':
                self.builder.call(self.scanf_fn, [self._global_str_ptr('%d'), ptr])
            elif typ == 'real':
                self.builder.call(self.scanf_fn, [self._global_str_ptr('%lf'), ptr])
            elif typ == 'str':
                buf = self._malloc_n(I8, ir.Constant(I64, 256), self.builder)
                self.builder.store(buf, ptr)
                self.builder.call(self.scanf_fn, [self._global_str_ptr('%255s'), buf])

    # ─── Casts ──────────────────────────────────────────────────────

    def _to_str(self, val, src_type):
        if src_type == 'str':
            return val
        if src_type == 'bool':
            true_ptr = self._global_str_ptr('true')
            false_ptr = self._global_str_ptr('false')
            return self.builder.select(self._to_i1(val), true_ptr, false_ptr)
        buf = self.builder.call(self.malloc_fn, [ir.Constant(I64, 32)])
        if src_type == 'int':
            self.builder.call(self.sprintf_fn, [buf, self._global_str_ptr('%d'), val])
        elif src_type == 'real':
            self.builder.call(self.sprintf_fn, [buf, self._global_str_ptr('%g'), val])
        return buf

    def _cast(self, target, val, src_type):
        if target == src_type:
            return val
        if target == 'str':
            return self._to_str(val, src_type)
        if target == 'int':
            if src_type == 'real':
                return self.builder.fptosi(val, I32)
            if src_type == 'bool':
                return self.builder.zext(val, I32)
            return val
        if target == 'real':
            if src_type == 'int':
                return self.builder.sitofp(val, F64)
            if src_type == 'bool':
                return self.builder.sitofp(self.builder.zext(val, I32), F64)
            return val
        if target == 'bool':
            if src_type == 'int':
                cmp = self.builder.icmp_signed('!=', val, ir.Constant(I32, 0))
                return self.builder.zext(cmp, I8)
            if src_type == 'real':
                cmp = self.builder.fcmp_ordered('!=', val, ir.Constant(F64, 0.0))
                return self.builder.zext(cmp, I8)
            return val
        return val

    # ─── Primary ────────────────────────────────────────────────────

    def visitPrimary(self, ctx):
        if ctx.INT_LIT() is not None:
            return ir.Constant(I32, int(ctx.INT_LIT().getText())), 'int'
        if ctx.REAL_LIT() is not None:
            return ir.Constant(F64, float(ctx.REAL_LIT().getText())), 'real'
        if ctx.STR_LIT() is not None:
            text = self._unescape(ctx.STR_LIT().getText())
            return self._global_str_ptr(text), 'str'

        first_text = ctx.getChild(0).getText() if ctx.getChildCount() > 0 else ''

        if first_text == 'true':
            return ir.Constant(I8, 1), 'bool'
        if first_text == 'false':
            return ir.Constant(I8, 0), 'bool'
        if first_text == 'null':
            return ir.Constant(I8P, None), 'null'
        if first_text == 'this':
            return self._this_stack[-1]

        if first_text == 'new':
            nome = ctx.IDENT().getText()
            class_info = self.lookup(nome)
            arg_vals = []
            if ctx.argList() is not None:
                for e in ctx.argList().expr():
                    arg_vals.append(self.visit(e))
            obj_ptr = self._malloc_n(class_info['struct'], ir.Constant(I64, 1), self.builder)
            for attr_name in class_info['attr_order']:
                a_idx, a_tipo, a_dims, a_base = class_info['atributos'][attr_name]
                if a_dims:
                    arr_ptr = self._alloc_array(a_dims, a_base, self.builder)
                    field_ptr = self.builder.gep(
                        obj_ptr, [ir.Constant(I32, 0), ir.Constant(I32, a_idx)], inbounds=True)
                    self.builder.store(arr_ptr, field_ptr)
            ctor = class_info['constructor']
            if ctor is not None:
                coerced = [self._coerce(v, t, pt) for (v, t), pt in zip(arg_vals, ctor['params'])]
                self.builder.call(ctor['llvm_func'], [obj_ptr] + coerced)
            return obj_ptr, nome

        if ctx.IDENT() is not None:
            nome = ctx.IDENT().getText()
            info = self.lookup(nome)
            cat = info.get('categoria')
            if cat in ('var', 'const', 'param'):
                return self.builder.load(info['ptr']), info['tipo']
            raise CodegenError(f"'{nome}' não é um valor")

        if ctx.castType() is not None:
            target = ctx.castType().getText()
            val, src_type = self.visit(ctx.expr(0))
            return self._cast(target, val, src_type), target

        if first_text == '(':
            return self.visit(ctx.expr(0))

        if first_text == '[':
            exprs = ctx.expr()
            if not exprs:
                return ir.Constant(I8P, None), '?[]'
            vals = [self.visit(e) for e in exprs]
            elem_type = vals[0][1]
            elem_llvm = self.llvm_type_for(elem_type)
            arr_ptr = self._malloc_n(elem_llvm, ir.Constant(I64, len(vals)), self.builder)
            for i, (v, t) in enumerate(vals):
                v2 = self._coerce(v, t, elem_type)
                slot = self.builder.gep(arr_ptr, [ir.Constant(I32, i)])
                self.builder.store(v2, slot)
            return arr_ptr, elem_type + '[]'

        raise CodegenError('primary inesperado')


def generate_module(tree, module_name='jss_module'):
    generator = LLVMCodeGenerator(module_name=module_name)
    module = generator.generate(tree)
    llvm_ir = str(module)
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()
    parsed = binding.parse_assembly(llvm_ir)
    parsed.verify()
    return llvm_ir


def run_jit(llvm_ir):
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = binding.parse_assembly('')
    engine = binding.create_mcjit_compiler(backing_mod, target_machine)

    mod = binding.parse_assembly(llvm_ir)
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()

    func_ptr = engine.get_function_address('main')
    cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)
    return cfunc()


def emit_object_code(llvm_ir):
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()
    mod = binding.parse_assembly(llvm_ir)
    mod.verify()
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine(reloc='pic', codemodel='default')
    return target_machine.emit_object(mod)


def compile_to_executable(llvm_ir, output_path, cc=None):
    cc = cc or shutil.which('cc') or shutil.which('gcc') or shutil.which('clang')
    if cc is None:
        raise CodegenError(
            "Nenhum linker/compilador C encontrado (cc, gcc ou clang). "
            "Instale um deles para gerar o executável."
        )

    obj_bytes = emit_object_code(llvm_ir)
    fd, obj_path = tempfile.mkstemp(suffix='.o')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(obj_bytes)
        result = subprocess.run(
            [cc, obj_path, '-o', output_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise CodegenError(f"Falha ao linkar executável:\n{result.stderr}")
    finally:
        os.unlink(obj_path)
    os.chmod(output_path, 0o755)
    return output_path
