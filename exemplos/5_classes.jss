// Testes de classes: atributos, construtores, metodos, arrays
// Esse teste tem função void main! Testar quem implementou essa opção

class Pessoa {
    str nome;
    int idade;
    
    Pessoa constructor(str n, int i) {
        this.nome = n;
        this.idade = i;
    }
    
    str getNome() {
        return this.nome;
    }
    
    int getIdade() {
        return this.idade;
    }
    
    void apresentar() {
        console.log("Nome:", this.nome, "Idade:", this.idade);
    }
    
    void aniversario() {
        this.idade = this.idade + 1;
        console.log(this.nome, "agora tem", this.idade, "anos");
    }
}

class Contador {
    int valor;
    
    Contador constructor() {
        this.valor = 0;
    }
    
    void incrementar() {
        this.valor = this.valor + 1;
    }
    
    void decrementar() {
        this.valor = this.valor - 1;
    }
    
    int getValor() {
        return this.valor;
    }
}

class MatrizHelper {
    int[3][3] matriz;
    
    MatrizHelper constructor() {
        // Inicializa matriz
        for (let int i = 0; i < 3; i = i + 1) {
            for (let int j = 0; j < 3; j = j + 1) {
                this.matriz[i][j] = 0;
            }
        }
    }
    
    void setValor(int i, int j, int valor) {
        this.matriz[i][j] = valor;
    }
    
    int getValor(int i, int j) {
        return this.matriz[i][j];
    }
    
    void imprimir() {
        for (let int i = 0; i < 3; i = i + 1) {
            for (let int j = 0; j < 3; j = j + 1) {
                console.log(this.matriz[i][j]);
            }
        }
    }
}

function void main() {
    // === Teste Pessoa ===
    let Pessoa p1 = new Pessoa("Joao", 30);
    p1.apresentar();
    
    let str nome = p1.getNome();
    console.log("Nome obtido:", nome);
    
    p1.aniversario();
    
    // === Teste Contador ===
    let Contador c = new Contador();
    console.log("Contador inicial:", c.getValor());
    
    c.incrementar();
    c.incrementar();
    console.log("Apos 2 incrementos:", c.getValor());
    
    c.decrementar();
    console.log("Apos 1 decremento:", c.getValor());
    
    // === Teste MatrizHelper ===
    let MatrizHelper mh = new MatrizHelper();
    mh.setValor(0, 0, 1);
    mh.setValor(0, 1, 2);
    mh.setValor(1, 0, 3);
    mh.setValor(1, 1, 4);
    
    let int val = mh.getValor(1, 1);
    console.log("Valor[1][1]:", val);
    
    console.log("Matriz:");
    mh.imprimir();
}
