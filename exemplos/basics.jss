// Testes de tipos basicos: variaveis, constantes, arrays

function void main() {
    // === VARIAVEIS ===
    let int x = 10;
    let real y = 3.14;
    let str nome = "Joao";
    let bool ativo = true;
    
    console.log("Int:", x);
    console.log("Real:", y);
    console.log("String:", nome);
    console.log("Bool:", ativo);
    
    // Multiplas declaracoes
    let int a, b, c;
    a = 5;
    b = 10;
    c = a + b;
    console.log("Soma:", c);
    
    // === CONSTANTES ===
    const int MAX = 100;
    const real PI = 3.14159;
    const str MSG = "Constante";
    console.log("Constantes:", MAX, PI, MSG);
    
    // === ARRAYS 1D ===
    let int[5] numeros;
    numeros[0] = 10;
    numeros[1] = 20;
    numeros[2] = 30;
    numeros[3] = 40;
    numeros[4] = 50;
    
    console.log("Array[0]:", numeros[0]);
    console.log("Array[4]:", numeros[4]);
    
    // Iterando array
    for (let int i = 0; i < 5; i = i + 1) {
        console.log("numeros[", i, "]:", numeros[i]);
    }
    
    // Atribuicao composta em arrays
    let int[3] arr;
    arr[0] = 10;
    arr[0] += 5;   // 15
    console.log("Array com +=:", arr[0]);
    
    arr[1] = 20;
    arr[1] *= 2;   // 40
    console.log("Array com *=:", arr[1]);
}
