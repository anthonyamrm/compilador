# Compilador JSS — JavaScript Simplificado

Compilador para a linguagem **JSS (JavaScript Simplificado)**, desenvolvido como projeto final da disciplina de Compiladores — UFPI 2026.1.

O compilador realiza análise léxica, sintática e semântica de programas escritos em JSS, reportando erros com o número de linha correspondente.

---

## Pré-requisitos

- Python 3.10+
- Java 11+ (para regenerar o lexer/parser via ANTLR4, se necessário)
- Biblioteca ANTLR4 para Python:

```bash
pip install antlr4-python3-runtime==4.13.2
```

---

## Estrutura do projeto

```
compilador/
├── JSS.g4                  # Gramática formal da linguagem JSS (ANTLR4)
├── JSSLexer.py             # Analisador léxico (gerado pelo ANTLR4)
├── JSSParser.py            # Analisador sintático (gerado pelo ANTLR4)
├── JSSVisitor.py           # Visitor base (gerado pelo ANTLR4)
├── error_listener.py       # Listener de erros léxicos e sintáticos
├── main.py                 # Ponto de entrada do compilador (CLI)
├── exemplos/               # Programas JSS de exemplo
│   ├── basics.jss          # Variáveis, constantes e arrays
│   ├── control_flow.jss    # if-else, for, while, break
│   └── operators.jss       # Operadores aritméticos, lógicos e relacionais
└── README.md
```

---

## Como executar

```bash
python3 main.py <arquivo.jss>
```

O compilador lê o arquivo `.jss` informado e imprime:

- `Compilação bem-sucedida.` — se o programa não contiver erros
- `Erro Léxico na linha X: <mensagem>` — para erros léxicos
- `Sintático na linha X: <mensagem>` — para erros sintáticos

---

## Testando os exemplos

### Programas válidos

```bash
python3 main.py exemplos/basics.jss
python3 main.py exemplos/control_flow.jss
python3 main.py exemplos/operators.jss
```

Saída esperada para todos:

```
Compilação bem-sucedida.
```

### Testando erros léxicos

Crie um arquivo com um caractere inválido para JSS:

```bash
cat > /tmp/erro_lexico.jss << 'EOF'
function void main() {
    let int x = 10@;
}
EOF
python3 main.py /tmp/erro_lexico.jss
```

Saída esperada:

```
Erro Léxico na linha 2: token recognition error at: '@'
```

### Testando erros sintáticos

Crie um arquivo com sintaxe inválida:

```bash
cat > /tmp/erro_sintatico.jss << 'EOF'
function void main() {
    let int x = ;
}
EOF
python3 main.py /tmp/erro_sintatico.jss
```

Saída esperada:

```
Erro Sintático na linha 2: mismatched input ';' expecting ...
```

---

## Regenerando o lexer e o parser

Caso o arquivo `JSS.g4` seja modificado, regenere os arquivos Python com:

```bash
java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor JSS.g4
```

---

## Linguagem JSS — Resumo

| Recurso | Exemplo |
|---|---|
| Variável | `let int x = 10;` |
| Constante | `const real PI = 3.14;` |
| Vetor | `let int[5] v;` |
| Função | `function int soma(int a, int b) { return a + b; }` |
| Classe | `class Ponto { int x; Ponto constructor(int x) { this.x = x; } }` |
| If-else | `if (x > 0) { ... } else { ... }` |
| While | `while (x < 10) { ... }` |
| For | `for (let int i = 0; i < 10; i = i + 1) { ... }` |
| Entrada | `input(x);` |
| Saída | `console.log("valor:", x);` |
| Casting | `int(3.9)` → `3` / `str(10 + 5)` → `"15"` |

Tipos primitivos: `int`, `real`, `str`, `bool`. Tipo de retorno especial: `void`.
