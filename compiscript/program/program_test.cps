
let numeros: integer[] = [1, 2, 3, 4, 5];  

foreach (n in numeros) { // <-- Se encuentra dentro de un ciclo
  if (n == 3) {
    continue;
  }
  print("Number: " + n);
  if (n > 4) {
    break;
  }
}

foreach (n in numeros) {
  if (n < 60) {
    continue;
  }
  if (n == 100) {
    break;
  }  
  print(n);
}