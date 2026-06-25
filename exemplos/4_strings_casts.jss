// Testes de strings: console.log, input, concatenacao, cast

// === PRINT com multiplos parametros ===
console.log("Ola", " ", "Mundo", "!");

let int x = 10;
let int y = 20;
console.log("x =", x, ", y =", y);

let str nome = "Joao";
let int idade = 25;
console.log("Nome:", nome, "Idade:", idade);

// === CONCATENACAO ===
let str saudacao = "Ola" + " " + "Mundo";
console.log(saudacao);

let str parte1 = "Hello";
let str parte2 = "World";
let str completo = parte1 + " " + parte2;
console.log(completo);

let str msg = "A soma de " + "5 e 3 e ";
console.log(msg, 8);

// === INPUT com multiplas variaveis ===
let int a, b, c;
console.log("Digite tres numeros:");
input(a, b, c);
console.log("Voce digitou:", a, b, c);

let str nome1, nome2;
console.log("Digite dois nomes:");
input(nome1, nome2);
console.log("Nomes:", nome1, "e", nome2);

// === CAST ===
// Int para Real
let int valor_int = 42;
let real valor_real = real(valor_int);
console.log("Int->Real:", valor_int, "->", valor_real);

// Real para Int
let real pi = 3.14;
let int pi_int = int(pi);
console.log("Real->Int:", pi, "->", pi_int);

// Para String
let str num_str = str(valor_int);
console.log("Int->String:", num_str);

// Para Bool
let int zero = 0;
let int nao_zero = 5;
let bool falso = bool(zero);
let bool verdadeiro = bool(nao_zero);
console.log("Int->Bool:", falso, verdadeiro);

// Cast em expressoes
let int result = int(5.5 + 4.5);
console.log("Cast expressao:", result);
