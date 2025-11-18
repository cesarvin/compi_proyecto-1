let resultado = 0;

function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}


let x = 5;

resultado = factorial(x);

print("resultado de factorial: ");
print(resultado);