from antlr4.error.ErrorListener import ErrorListener


class JSSErrorListener(ErrorListener):
    def __init__(self, error_type):
        super().__init__()
        self.errors = []
        self.error_type = error_type  # 'Léxico' ou 'Sintático'

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"Erro {self.error_type} na linha {line}: {msg}")

    def add_error(self, line, msg):
        self.errors.append(f"Erro {self.error_type} na linha {line}: {msg}")

    def has_errors(self):
        return len(self.errors) > 0
