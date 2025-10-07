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