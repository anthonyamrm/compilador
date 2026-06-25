# Compilador JSS — JavaScript Simplificado

Compilador para a linguagem **JSS (JavaScript Simplificado)**, desenvolvido como projeto final da disciplina de Compiladores — UFPI 2026.1.

O front-end realiza **análise léxica, sintática e semântica** de programas escritos em JSS, reportando erros com o número de linha correspondente.

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
├── error_listener.py       # Listener de erros (léxico/sintático/semântico)
├── semantic_analyzer.py    # Analisador semântico (Visitor customizado)
├── main.py                 # Ponto de entrada (CLI)
├── exemplos/               # Programas JSS de exemplo
│   ├── 1_basics.jss
│   ├── 2_operators.jss
│   ├── 3_control_flow.jss
│   ├── 4_strings_casts.jss
│   ├── 5_classes.jss
│   ├── 6_functions.jss
│   ├── 7_errors.jss        # Programas com erros léxicos/sintáticos
│   └── 8_erros_funcao.jss  # Programas com erros em funções
└── README.md
```

---

## Como executar

O compilador aceita o programa de duas formas:

```bash
# Passando o arquivo como argumento
python3 main.py exemplos/1_basics.jss

# Lendo da entrada padrão (stdin)
python3 main.py < exemplos/1_basics.jss
```

Saídas possíveis:

- `Compilação bem-sucedida.` — programa válido
- `Erro Léxico na linha X: <mensagem>` — erro léxico
- `Erro Sintático na linha X: <mensagem>` — erro sintático
- `Erro Semântico na linha X: <mensagem>` — erro semântico

---

## Testando os exemplos

### Programas válidos

```bash
python3 main.py exemplos/1_basics.jss
python3 main.py exemplos/3_control_flow.jss
python3 main.py exemplos/4_strings_casts.jss
python3 main.py exemplos/5_classes.jss
```

### Testando erros léxicos

```bash
cat > /tmp/erro_lexico.jss << 'EOF'
function void main() {
    let int x = 10@;
}
EOF
python3 main.py /tmp/erro_lexico.jss
```

Saída esperada: `Erro Léxico na linha 2: token recognition error at: '@'`

### Testando erros sintáticos

```bash
cat > /tmp/erro_sintatico.jss << 'EOF'
function void main() {
    let int x = ;
}
EOF
python3 main.py /tmp/erro_sintatico.jss
```

Saída esperada: `Erro Sintático na linha 2: ...`

### Testando erros semânticos

```bash
# Tipo incompatível em atribuição
echo 'function void main() { let int x = "abc"; }' | python3 main.py
# → Erro Semântico na linha 1: não é possível inicializar 'x' (tipo 'int') com valor do tipo 'str'

# Variável não declarada
echo 'function void main() { console.log(naoExiste); }' | python3 main.py
# → Erro Semântico na linha 1: identificador 'naoExiste' não declarado

# Condição não-bool em if
echo 'function void main() { if (5) { } }' | python3 main.py
# → Erro Semântico na linha 1: condição de 'if' deve ser 'bool', recebeu 'int'

# Atribuir a const
echo 'function void main() { const int N = 5; N = 10; }' | python3 main.py
# → Erro Semântico na linha 1: não é possível atribuir à constante 'N'

# Função sem return
echo 'function int foo(int x) { let int y = x * 2; }' | python3 main.py
# → Erro Semântico na linha 1: função 'foo' deve retornar um valor do tipo 'int'

# Argumentos de função errados
echo 'function int dobro(int x) { return x * 2; }
function void main() { let int v = dobro("oi"); }' | python3 main.py
# → Erro Semântico na linha 2: argumento 1 de função 'dobro': esperado 'int', recebeu 'str'
```

---

## Regras semânticas verificadas

O analisador semântico cobre:

- **Identificadores e escopo**: redeclaração no mesmo escopo, uso sem declaração, escopos aninhados (função, bloco, for)
- **Constantes**: atribuição em `const`, alteração de atributos de objeto const, alteração de elementos de vetor const
- **Tipos**: sistema de tipos completo conforme Tabela 1 do PDF (precedência de operadores e tipos aceitos)
- **Conversão implícita**: `int → real` em operadores e atribuição; `+ str` para concatenação
- **Funções**: nome único, parâmetros, return obrigatório, tipo de retorno bate com a expressão, tipo de retorno não pode ser vetor, validação de argumentos em chamadas
- **Classes**: atributos antes de métodos, construtor obrigatório, `new` com argumentos corretos, `this`, acesso a atributos/métodos, const objeto
- **Controle de fluxo**: condição de `if/while/for` deve ser `bool`, `break` só dentro de loop
- **Vetores**: índice `int`, base deve ser vetor, literal de vetor só na inicialização
- **Funções nativas**: `input(vars)` recebe variáveis int/real/str; `console.log(...)` recebe primitivos; casts validam operandos

---

## Regenerando o lexer e o parser

Se `JSS.g4` for modificado, regenere os arquivos Python com:

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
| If-else | `if (x > 0) { ... } else if (x < 0) { ... } else { ... }` |
| While | `while (x < 10) { ... }` |
| For | `for (let int i = 0; i < 10; i = i + 1) { ... }` |
| Entrada | `input(x);` |
| Saída | `console.log("valor:", x);` |
| Casting | `int(3.9)` → `3` / `str(10 + 5)` → `"15"` |

Tipos primitivos: `int`, `real`, `str`, `bool`. Tipo de retorno especial: `void`.
