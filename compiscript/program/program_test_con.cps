let a: integer = 15;
let x: integer = 0;

if (a > 10) {
  print("en el if");
  x = 1;
} else {
  x = 2;
}
print (x);

a = 5;
if (a > 10) {
  x = 1;
} else {
  print("en el else");
  x = 2;
}
print (x);

print ("fin if");

let i = 0;
while (i < 5) {
  i = i + 1;  
  print("en el while");
  print(i);
}
print ("fin while");

i = 0;
do {
  i = i + 1;
  print("en el do");
  print(i);
} while (i < 3);

print ("fin do while");

for (let j = 0; j < 5; j = j + 1) {
  print("en el for");
  print(j);
}
print ("fin for");