import argparse
import os
import sys

from antlr4 import CommonTokenStream, InputStream
from JSSLexer import JSSLexer
from JSSParser import JSSParser
from error_listener import JSSErrorListener
from semantic_analyzer import SemanticAnalyzer
from backend import generate_module, run_jit, compile_to_executable, CodegenError


def compile(source):
    """Roda léxico/sintático/semântico. Devolve a árvore em caso de sucesso
    (imprimindo os erros e devolvendo None em caso de falha)."""
    input_stream = InputStream(source)

    lexer = JSSLexer(input_stream)
    lexer.removeErrorListeners()
    lexer_errors = JSSErrorListener('Léxico')
    lexer.addErrorListener(lexer_errors)

    token_stream = CommonTokenStream(lexer)

    parser = JSSParser(token_stream)
    parser.removeErrorListeners()
    parser_errors = JSSErrorListener('Sintático')
    parser.addErrorListener(parser_errors)

    tree = parser.program()

    if lexer_errors.has_errors():
        for err in lexer_errors.errors:
            print(err)
        return None

    if parser_errors.has_errors():
        for err in parser_errors.errors:
            print(err)
        return None

    analyzer = SemanticAnalyzer()
    analyzer.analyze(tree)
    if analyzer.errors.has_errors():
        for err in analyzer.errors.errors:
            print(err)
        return None

    return tree


def main():
    parser = argparse.ArgumentParser(description='Compilador JSS (JavaScript Simplificado)')
    parser.add_argument('arquivo', nargs='?', help='arquivo .jss de entrada (padrão: stdin)')
    parser.add_argument('-o', '--output', help='caminho do arquivo .ll de saída')
    parser.add_argument('--emit-llvm', action='store_true',
                         help='imprime o LLVM IR gerado no stdout')
    parser.add_argument('--run', action='store_true',
                         help='executa o programa via JIT (llvmlite) após gerar o IR')
    parser.add_argument('--exe', nargs='?', const='__default__', default=None,
                         metavar='SAIDA',
                         help='gera um executável nativo (link via cc/gcc/clang); '
                              'aceita opcionalmente o caminho de saída')
    args = parser.parse_args()

    if args.arquivo:
        try:
            with open(args.arquivo, 'r', encoding='utf-8') as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {args.arquivo}")
            sys.exit(1)
    else:
        source = sys.stdin.read()

    tree = compile(source)
    if tree is None:
        sys.exit(1)

    print("Compilado!")

    try:
        llvm_ir = generate_module(tree, module_name=args.arquivo or 'jss_stdin')
    except Exception as exc:
        print(f"Erro ao gerar LLVM IR: {exc}")
        sys.exit(1)

    if args.output:
        out_path = args.output
    elif args.arquivo:
        out_path = os.path.splitext(args.arquivo)[0] + '.ll'
    else:
        out_path = 'out.ll'

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(llvm_ir)
    print(f"LLVM IR gerado em: {out_path}")

    if args.emit_llvm:
        print(llvm_ir)

    if args.exe is not None:
        if args.exe == '__default__':
            exe_path = os.path.splitext(args.arquivo)[0] if args.arquivo else 'a.out'
        else:
            exe_path = args.exe
        try:
            compile_to_executable(llvm_ir, exe_path)
        except CodegenError as exc:
            print(exc)
            sys.exit(1)
        print(f"executavel gerado em:{exe_path}")

    if args.run:
        exit_code = run_jit(llvm_ir)
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
