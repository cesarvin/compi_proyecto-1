// Recursion
function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}


let x = 4;
let resultado = 0;

resultado = factorial(x);

print(resultado);

