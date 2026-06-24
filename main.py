import sys
from antlr4 import CommonTokenStream, FileStream, InputStream
from JSSLexer import JSSLexer
from JSSParser import JSSParser
from error_listener import JSSErrorListener


def compile(source):
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
        return False

    if parser_errors.has_errors():
        for err in parser_errors.errors:
            print(err)
        return False

    return tree


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 main.py <arquivo.jss>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {filename}")
        sys.exit(1)

    result = compile(source)

    if result:
        print("Compilação bem-sucedida.")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
