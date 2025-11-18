class Punto {
  let x: integer;
  let y: integer;
}

let p: Punto = new Punto();

p.x = 50;
p.y = 100;

print(p.x);
print(p.y);

let p2: Punto = new Punto();
p2.x = 2;
print(p2.x);

let p3: Punto = new Punto();
p3.x = 2;
print(p3.x);

let sumx: integer = p.x * p2.x * p3.x;

print ("sumx es ");
print (sumx);