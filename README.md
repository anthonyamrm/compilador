# Compilador JSS — JavaScript Simplificado

Compilador para a linguagem **JSS (JavaScript Simplificado)**, desenvolvido como projeto final da disciplina de Compiladores — UFPI 2026.1.

O front-end realiza **análise léxica, sintática e semântica** de programas escritos em JSS, reportando erros com o número de linha correspondente. O back-end gera **LLVM IR** a partir da árvore validada e pode executar o programa via JIT.

---

## Pré-requisitos

- Python 3.10+
- Java 11+ (para regenerar o lexer/parser via ANTLR4, se necessário)
- Dependências Python (ANTLR4 runtime + [llvmlite](https://llvmlite.readthedocs.io/), usada para gerar/verificar/executar o LLVM IR):

```bash
pip install -r requirements.txt
```

- (Opcional, só para `--exe`) um compilador/linker C no sistema — `cc`,
  `gcc` ou `clang`, usado apenas para linkar o objeto gerado pelo llvmlite
  contra a libc.

Não é necessário ter `clang`/`llc` instalados: o `llvmlite` já traz o LLVM embutido, tanto para verificar o IR gerado quanto para executá-lo via JIT (`--run`).

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
├── codegen.py               # Backend: geração de LLVM IR + execução via JIT
├── main.py                 # Ponto de entrada (CLI)
├── requirements.txt         # Dependências Python
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

Quando a compilação é bem-sucedida, o backend (`codegen.py`) gera o **LLVM IR**
correspondente e grava num arquivo `.ll` ao lado da entrada (ex.:
`exemplos/1_basics.jss` → `exemplos/1_basics.ll`). Flags adicionais:

| Flag | Efeito |
|---|---|
| `-o ARQUIVO` | grava o `.ll` num caminho customizado em vez do padrão |
| `--emit-llvm` | também imprime o LLVM IR gerado no stdout |
| `--run` | executa o programa via JIT (llvmlite) logo após gerar o IR |
| `--exe [SAIDA]` | gera um **executável nativo** (ver abaixo) |

```bash
# Gera exemplos/5_classes.ll e roda o programa via JIT
python3 main.py exemplos/5_classes.jss --run

# Só imprime o IR no stdout (sem rodar)
python3 main.py exemplos/6_functions.jss --emit-llvm

# Gera um executável nativo (exemplos/6_functions) e roda
python3 main.py exemplos/6_functions.jss --exe
./exemplos/6_functions

# Caminho de saída customizado para o executável
python3 main.py exemplos/6_functions.jss --exe /tmp/prog
```

Não é preciso ter `clang`/`llc` instalados — o `llvmlite` já embute o LLVM
necessário para gerar o IR, verificar (`module.verify()`), executar via JIT
(`--run`) e até compilar para código de máquina nativo (`--exe`). A única
ferramenta externa usada é o **linker do sistema** (`cc`/`gcc`/`clang`, o que
estiver disponível) na etapa final de `--exe`, para transformar o `.o` gerado
pelo llvmlite num executável ligado à libc (`printf`, `malloc`, etc.).

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
- **Funções**: nome único, parâmetros, return obrigatório, tipo de retorno bate com a expressão (incluindo retorno de vetor), validação de argumentos em chamadas
- **Classes**: atributos antes de métodos, construtor obrigatório, `new` com argumentos corretos, `this`, acesso a atributos/métodos, const objeto
- **Controle de fluxo**: condição de `if/while/for` deve ser `bool`, `break` só dentro de loop
- **Vetores**: índice `int`, base deve ser vetor, literal de vetor só na inicialização
- **Funções nativas**: `input(vars)` recebe variáveis int/real/str; `console.log(...)` recebe primitivos; casts validam operandos

---

## Backend: geração de LLVM IR

`codegen.py` implementa `LLVMCodeGenerator`, um segundo *visitor* sobre a
mesma árvore ANTLR (`JSSVisitor`/`JSSParser`), estruturado como o
`SemanticAnalyzer` (mesma pilha de escopos), mas que emite instruções LLVM
via [`llvmlite`](https://llvmlite.readthedocs.io/) em vez de só inferir
tipos. Só roda sobre programas que já passaram na análise semântica.

Mapeamento de tipos JSS → LLVM:

| JSS | LLVM |
|---|---|
| `int` | `i32` |
| `real` | `double` |
| `bool` | `i8` (0/1) |
| `str` | `i8*` (string C, sempre alocada no heap) |
| `ClassName` | `%ClassName*` (struct nomeado, sempre heap-alocado) |
| `T[]` | `T_llvm*` (bloco malloc'ado; multi-dimensional = ponteiro de ponteiro, uma malloc por dimensão) |

Pontos relevantes da implementação:

- **Sem `free`**: não há coletor de lixo nem liberação manual — cada `new`,
  cada array e cada resultado de concatenação de string aloca memória via
  `malloc` que nunca é liberada. Aceitável para o escopo do trabalho, mas é
  uma limitação conhecida.
- **`console.log`/`input`** usam `printf`/`scanf` da libc (declaradas como
  `extern` no módulo), com formato escolhido pelo tipo de cada argumento.
- **Concatenação de strings** (`+`) e **potência** (`**`) usam funções
  auxiliares geradas uma vez no módulo (`jss_str_concat`, `jss_ipow`), já
  que o LLVM não tem instruções nativas para elas.
- **`&&`/`||`** são gerados com curto-circuito real (branches + `phi`), não
  avaliação ansiosa dos dois operandos.
- O ponto de entrada real (`main() -> i32`, ABI C) executa, em ordem, todo
  código de nível superior (variáveis/`console.log`/laços fora de função) e,
  ao final, chama a função do usuário chamada `main` (se existir) — cobrindo
  tanto exemplos "de script" (sem função `main`) quanto os que colocam tudo
  dentro de `function void main()`.

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
