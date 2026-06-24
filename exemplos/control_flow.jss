// Testes de estruturas de controle: if, for, while, break

function void main() {
    // === IF-ELSE ===
    let int idade = 20;
    if (idade >= 18) {
        console.log("Maior de idade");
    } else {
        console.log("Menor de idade");
    }
    
    // IF-ELSE IF-ELSE
    let int nota = 7;
    if (nota >= 9) {
        console.log("A");
    } else if (nota >= 7) {
        console.log("B");
    } else if (nota >= 5) {
        console.log("C");
    } else {
        console.log("F");
    }
    
    // === FOR ===
    let int soma = 0;
    for (let int i = 1; i <= 10; i = i + 1) {
        soma += i;
    }
    console.log("Soma 1-10:", soma);
    
    // FOR aninhado
    for (let int x = 0; x < 3; x = x + 1) {
        for (let int y = 0; y < 2; y = y + 1) {
            console.log("x:", x, "y:", y);
        }
    }
    
    // === WHILE ===
    let int contador = 0;
    while (contador < 5) {
        console.log("Contador:", contador);
        contador = contador + 1;
    }
    
    // WHILE com BREAK
    let int j = 0;
    while (true) {
        if (j == 3) {
            break;
        }
        console.log("j:", j);
        j = j + 1;
    }
    
    // WHILE aninhado
    let int a = 0;
    while (a < 2) {
        let int b = 0;
        while (b < 3) {
            console.log("a:", a, "b:", b);
            b = b + 1;
        }
        a = a + 1;
    }
}
