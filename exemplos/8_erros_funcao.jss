// Testes de erros semanticos em funcoes (arquivo deve falhar na compilacao)

// ERRO: funcao int sem return
function int semReturn() {
    let int x = 10;
    console.log(x);
}

// ERRO: funcao void com return de valor
function void voidComValor() {
    return 10;
}

// ERRO: funcao int com return sem valor
function int intSemValor() {
    return;
}

// ERRO: tipo de retorno incompativel
function int tipoRetornoErrado() {
    return "string";
}

// ERRO: funcao str sem return
function str strSemReturn() {
    let str s = "hello";
    console.log(s);
}


// Funcao com multiplos parametros
function real calcularMedia(int a, int b, int c) {
    let int soma = a + b + c;
    return real(soma) / 3.0;
}

// ERRO: chamada funcao nao declarada
funcaoInexistente();

// ERRO: parâmetro incorreto quantidade
calcularMedia(2, 3)

// ERRO: parâmetro incorreto tipo
calcularMedia(2, 3, 4.0)

// ERRO: parâmetro incorreto tipo e quantidade
calcularMedia(2.0, 3.0)
