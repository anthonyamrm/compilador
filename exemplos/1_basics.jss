// Testes de tipos basicos: variaveis, constantes, arrays

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

// === ARRAYS 2D ===
let int[3][3] matriz;
matriz[0][0] = 1;
matriz[0][1] = 2;
matriz[0][2] = 3;
matriz[1][0] = 4;
matriz[1][1] = 5;
matriz[1][2] = 6;
matriz[2][0] = 7;
matriz[2][1] = 8;
matriz[2][2] = 9;

console.log("Matriz[1][1]:", matriz[1][1]);

// Atribuicao composta em arrays
let int[3] arr;
arr[0] = 10;
arr[0] += 5;   // 15
console.log("Array com +=:", arr[0]);

arr[1] = 20;
arr[1] *= 2;   // 40
console.log("Array com *=:", arr[1]);
