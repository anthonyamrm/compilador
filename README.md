# Compilador JSS — JavaScript Simplificado

Compilador para a linguagem **JSS (JavaScript Simplificado)**, desenvolvido como projeto final da disciplina de Compiladores — UFPI 2026.1.

O front-end realiza **análise léxica, sintática e semântica** de programas escritos em JSS, reportando erros com o número da linha correspondente. O back-end (`backend.py`) gera **LLVM IR** a partir da árvore validada, podendo executar o programa via JIT ou gerar um executável nativo.

---

## 1. Requisitos de bibliotecas

### Software necessário

| Requisito | Versão | Para quê |
|---|---|---|
| Python | 3.10+ | executar o compilador |
| Java | 11+ | *(opcional)* apenas para regenerar o lexer/parser a partir da gramática `JSS.g4` |
| `cc`/`gcc`/`clang` | qualquer | *(opcional)* apenas para a flag `--exe` (linkar o executável nativo contra a libc) |

### Bibliotecas Python (`requirements.txt`)

| Biblioteca | Versão | Função |
|---|---|---|
| `antlr4-python3-runtime` | 4.13.2 | runtime do ANTLR4, usado pelo lexer/parser gerados (`JSSLexer.py`, `JSSParser.py`) |
| `llvmlite` | 0.47.0 | geração, verificação e execução (JIT) do LLVM IR no back-end |

Instalação:

```bash
pip install -r requirements.txt
```

> **Nota:** não é necessário ter `clang`/`llc` instalados — o `llvmlite` já embute o LLVM necessário para gerar o IR, verificá-lo e executá-lo via JIT (`--run`). A única ferramenta externa é o linker do sistema, usado somente na etapa final de `--exe`.

---

## 2. Comandos para executar o projeto

O compilador aceita o programa de duas formas:

```bash
# Passando o arquivo como argumento
python3 main.py exemplos/1_basics.jss

# Lendo da entrada padrão (stdin)
python3 main.py < exemplos/1_basics.jss
```

Quando a compilação é bem-sucedida, o LLVM IR é gravado num arquivo `.ll` ao lado da entrada (ex.: `exemplos/1_basics.jss` → `exemplos/1_basics.ll`).

### Flags disponíveis

| Flag | Efeito |
|---|---|
| `-o ARQUIVO` | grava o `.ll` num caminho customizado em vez do padrão |
| `--emit-llvm` | também imprime o LLVM IR gerado no stdout |
| `--run` | executa o programa via JIT (llvmlite) logo após gerar o IR |
| `--exe [SAIDA]` | gera um executável nativo (linka via `cc`/`gcc`/`clang`) |

```bash
# Compila e executa o programa via JIT
python3 main.py exemplos/1_basics.jss --run

# Só imprime o IR no stdout (sem rodar)
python3 main.py exemplos/6_functions.jss --emit-llvm

# Gera um executável nativo (exemplos/6_functions) e roda
python3 main.py exemplos/6_functions.jss --exe
./exemplos/6_functions

# Caminho de saída customizado para o executável
python3 main.py exemplos/6_functions.jss --exe /tmp/prog
```

### Regenerando o lexer/parser (opcional)

Só é necessário se a gramática `JSS.g4` for modificada:

```bash
java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor JSS.g4
```

---

## 3. Execução com exemplos

### ✅ Exemplo de sucesso

```bash
python3 main.py exemplos/1_basics.jss --run
```

Saída:

```
Compilado!
LLVM IR gerado em: exemplos/1_basics.ll
Int: 10
Real: 3.14
String: Joao
Bool: true
Soma: 15
Constantes: 100 3.14159 Constante
Array[0]: 10
Array[4]: 50
Matriz[1][1]: 5
Array com +=: 15
Array com *=: 40
```

Outros programas válidos disponíveis em `exemplos/`:

```bash
python3 main.py exemplos/2_operators.jss --run
python3 main.py exemplos/3_control_flow.jss --run
python3 main.py exemplos/4_strings_casts.jss --run
python3 main.py exemplos/5_classes.jss --run
python3 main.py exemplos/6_functions.jss --run
```

### ❌ Exemplo de erro léxico

Programa com caractere inválido (`@`):

```bash
echo 'let int x = 10@;' | python3 main.py
```

Saída:

```
Erro Léxico na linha 1: token recognition error at: '@'
```

### ❌ Exemplo de erro sintático

Declaração sem expressão após o `=`:

```bash
echo 'let int x = ;' | python3 main.py
```

Saída:

```
Erro Sintático na linha 1: mismatched input ';' expecting {'[', '(', 'int', 'real', 'str', 'bool', '+', '-', '!', '++', '--', 'true', 'false', 'null', 'this', 'new', REAL_LIT, INT_LIT, STR_LIT, IDENT}
```

### ❌ Exemplos de erro semântico

O arquivo `exemplos/7_errors.jss` concentra vários erros semânticos:

```bash
python3 main.py exemplos/7_errors.jss
```

Saída (trecho):

```
Erro Semântico na linha 6: identificador 'y' não declarado
Erro Semântico na linha 9: identificador 'x' já declarado neste escopo
Erro Semântico na linha 12: não é possível inicializar 's' (tipo 'str') com valor do tipo 'int'
Erro Semântico na linha 16: não é possível atribuir à constante 'c'
Erro Semântico na linha 19: 'break' fora de um loop
Erro Semântico na linha 27: cast 'int()' requer operando numérico ou 'bool', recebeu 'str'
Erro Semântico na linha 33: operador '+' requer dois operandos 'str' para concatenação, recebeu 'str' e 'int'
Erro Semântico na linha 46: 'this' usado fora de uma classe
```

Casos individuais via stdin:

```bash
# Tipo incompatível em atribuição
echo 'let int x = "abc";' | python3 main.py
# → Erro Semântico na linha 1: não é possível inicializar 'x' (tipo 'int') com valor do tipo 'str'

# Variável não declarada
echo 'console.log(naoExiste);' | python3 main.py
# → Erro Semântico na linha 1: identificador 'naoExiste' não declarado

# Argumento de função com tipo errado
printf 'function int dobro(int x) { return x * 2; }\nlet int v = dobro("oi");\n' | python3 main.py
# → Erro Semântico na linha 2: argumento 1 de função 'dobro': esperado 'int', recebeu 'str'
```

Também há erros de funções em `exemplos/8_erros_funcao.jss`:

```bash
python3 main.py exemplos/8_erros_funcao.jss
```

### Resumo das saídas possíveis

| Situação | Saída |
|---|---|
| Programa válido | `Compilado!` + `LLVM IR gerado em: <arquivo>.ll` (exit code 0) |
| Erro léxico | `Erro Léxico na linha X: <mensagem>` (exit code 1) |
| Erro sintático | `Erro Sintático na linha X: <mensagem>` (exit code 1) |
| Erro semântico | `Erro Semântico na linha X: <mensagem>` (exit code 1) |

---

## Estrutura do projeto

```
compilador/
├── JSS.g4                  # Gramática formal da linguagem JSS (ANTLR4)
├── JSSLexer.py             # Analisador léxico (gerado pelo ANTLR4)
├── JSSParser.py            # Analisador sintático (gerado pelo ANTLR4)
├── JSSVisitor.py           # Visitor base (gerado pelo ANTLR4)
├── JSSListener.py          # Listener base (gerado pelo ANTLR4)
├── error_listener.py       # Listener de erros (léxico/sintático/semântico)
├── semantic_analyzer.py    # Analisador semântico (Visitor customizado)
├── backend.py              # Back-end: geração de LLVM IR + JIT + executável
├── main.py                 # Ponto de entrada (CLI)
├── requirements.txt        # Dependências Python
├── antlr-4.13.2-complete.jar  # ANTLR4 (para regenerar lexer/parser)
├── exemplos/               # Programas JSS de exemplo
│   ├── 1_basics.jss        # variáveis, constantes, arrays
│   ├── 2_operators.jss     # operadores
│   ├── 3_control_flow.jss  # if/while/for/break
│   ├── 4_strings_casts.jss # strings e casts
│   ├── 5_classes.jss       # classes, construtor, this, new
│   ├── 6_functions.jss     # funções
│   ├── 7_errors.jss        # programas com erros semânticos
│   └── 8_erros_funcao.jss  # erros em funções
└── README.md
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
| If-else | `if (x > 0) { ... } else if (x < 0) { ... } else { ... }` |
| While | `while (x < 10) { ... }` |
| For | `for (let int i = 0; i < 10; i = i + 1) { ... }` |
| Entrada | `input(x);` |
| Saída | `console.log("valor:", x);` |
| Casting | `int(3.9)` → `3` / `str(10 + 5)` → `"15"` |

Tipos primitivos: `int`, `real`, `str`, `bool`. Tipo de retorno especial: `void`.
