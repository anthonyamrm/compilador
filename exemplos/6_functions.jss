// Testes de funcoes: declaracao, chamada, parametros, return, arrays

// Funcao simples
function int soma(int a, int b) {
    return a + b;
}

// Funcao void
function void imprimirMensagem(str msg) {
    console.log("Mensagem:", msg);
}

// Funcao com multiplos parametros
function real calcularMedia(int a, int b, int c) {
    let int soma = a + b + c;
    return real(soma) / 3.0;
}

// Funcao que retorna bool
function bool ehPar(int n) {
    return (n % 2) == 0;
}

// Funcao que retorna string
function str getNomeCompleto(str nome, str sobrenome) {
    return nome + " " + sobrenome;
}

// Funcao com array como parametro
function int somarArray(int[5] arr) {
    let int total = 0;
    for (let int i = 0; i < 5; i = i + 1) {
        total += arr[i];
    }
    return total;
}

// Funcao que retorna array
function int[5] criarSequencia(int inicio) {
    let int[5] seq;
    for (let int i = 0; i < 5; i = i + 1) {
        seq[i] = inicio + i;
    }
    return seq;
}

// Funcao recursiva (fatorial)
function int fatorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * fatorial(n - 1);
}

// Funcao void com return vazio
function void processar() {
    console.log("Processando...");
    return;
}

function void main() {
    // Testando funcoes
    let int resultado = soma(5, 3);
    console.log("Soma:", resultado);

    imprimirMensagem("Ola Mundo");

    let real media = calcularMedia(8, 7, 9);
    console.log("Media:", media);

    let bool par = ehPar(10);
    console.log("10 eh par?", par);

    let str nomeCompleto = getNomeCompleto("Joao", "Silva");
    console.log("Nome:", nomeCompleto);

    // Array em funcao
    let int[5] numeros;
    numeros[0] = 10;
    numeros[1] = 20;
    numeros[2] = 30;
    numeros[3] = 40;
    numeros[4] = 50;
    let int total = somarArray(numeros);
    console.log("Total:", total);

    // Funcao que retorna array
    let int[5] sequencia = criarSequencia(100);
    console.log("Sequencia[0]:", sequencia[0]);
    console.log("Sequencia[4]:", sequencia[4]);

    // Recursao
    let int fat5 = fatorial(5);
    console.log("Fatorial de 5:", fat5);

    // Void com return
    processar();
}
