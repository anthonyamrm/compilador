// Testes de operadores: aritmeticos, logicos, relacionais, atribuicao

function void main() {
    // === OPERADORES ARITMETICOS ===
    let int a = 10;
    let int b = 3;
    
    console.log("Soma:", a + b);           // 13
    console.log("Subtracao:", a - b);      // 7
    console.log("Multiplicacao:", a * b);  // 30
    console.log("Divisao:", a / b);        // 3
    console.log("Modulo:", a % b);         // 1
    console.log("Potencia:", a ** b ** 2);      // 10^9 = 1_000_000_000
    
    // Operadores unarios
    let int x = 5;
    console.log("Negacao:", -x);           // -5
    console.log("Incremento:", ++x);       // 6
    console.log("Decremento:", --x);       // 5
    
    // Mistura int e real
    let real r = 3.5;
    console.log("Int + Real:", a + r);     // 13.5 (real)
    
    // === OPERADORES LOGICOS ===
    let bool t = true;
    let bool f = false;
    
    console.log("AND:", t && f);           // false
    console.log("OR:", t || f);            // true
    console.log("NOT:", !t);               // false
    
    // === OPERADORES RELACIONAIS ===
    let int n1 = 10;
    let int n2 = 5;
    
    console.log("Maior:", n1 > n2);        // true
    console.log("Menor:", n1 < n2);        // false
    console.log("Igual:", n1 == n2);       // false
    console.log("Diferente:", n1 != n2);   // true
    console.log("MaiorIgual:", n1 >= n2);  // true
    console.log("MenorIgual:", n1 <= n2);  // false
    
    // === ATRIBUICAO COMPOSTA ===
    let int val = 10;
    
    val += 5;   // 15
    console.log("+=", val);
    
    val -= 3;   // 12
    console.log("-=", val);
    
    val *= 2;   // 24
    console.log("*=", val);
    
    val /= 4;   // 6
    console.log("/=", val);
    
    val %= 4;   // 2
    console.log("%=", val);
    
    // Atribuicao composta com bool
    let bool flag = true;
    flag &&= false;  // false
    console.log("&&=", flag);
    
    flag ||= true;   // true
    console.log("||=", flag);
}
