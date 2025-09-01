function testClosureScoping() : integer {

    let contador : integer = 0;

    function incrementar() : integer {
        contador = contador + 1; 
        return contador;
    }

    incrementar();

    return incrementar(); 
}


const resultado = testClosureScoping(); 

// Class definition and usage
class Animal {
  let name: string;

  function constructor(name: string) {
    this.name = name;
  }

  function speak(): string {
    return this.name + " makes a sound.";
  }
}

class Dog : Animal {
  function speak(): string {
    return this.name + " barks.";
  }
}

let dog: Dog = new Dog("Rex");
print(dog.speak());