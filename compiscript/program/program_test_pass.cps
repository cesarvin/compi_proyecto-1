let a: integer;
a = 2* 8;
let x = a + 5;

print(x + 5);



// Recursion
function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}

class Dog {
  let name: string;

  function constructor(name: string) {
    this.name = name;
  }

  function speak(): string {
    return this.name + " makes a sound.";
  }
}

let dog: Dog = new Dog("Rex");

let dog2: Dog = new Dog("snoopy");

let numbers: integer[] = [10, 20, 30];

foreach (num in numbers) {
  print(num);
}


let dia = 2;
switch (dia) {
  case 1:
    print("Lunes");
    break;
  case 2:
    print("Martes");
    break;
  default:
    print("Otro");
    break;
}


try {
  print("Intentando...");
} catch (e) {
  print("Error atrapado.");
}

class User {
  let name: string;
  let age: integer;
}

// Creamos una instancia de la clase
let user1: User = new User();

// Asignamos valores a sus propiedades
user1.name = "Alice";
user1.age = 30;

print(user1.name);