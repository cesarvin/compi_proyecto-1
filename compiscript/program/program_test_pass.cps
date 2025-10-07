let a: integer;
a = 2* 8;
let x = a + 5;

print(x + 5);

if (a > 10) {
  x = 1;
} else {
  x = 2;
}

let i = 0;
while (i < 2) {
  i = i + 1;
  
  print(i);
}

let i = 0;
do {
  i = i + 1;
} while (i < 3);

for (let i = 0; i < 2; i = i + 1) {
  print(i);
}

// Recursion
function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}