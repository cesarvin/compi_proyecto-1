let c: integer;
let a: integer;
let b: integer;

c = 5+12;

if ((a == b) || (c != 15) && (a < 30)) {
    
    let d: string; 

    d = "dentro del if";

    print(d); 
} else {
    let e: string; 
    e = "dentro del else";
    print("Menor o igual");
}

while ((a == b) || (c != 15) && (a < 30)) {
     let var_en_while: string; 

    var_en_while = "dentro del while";

    print (var_en_while);
}

do {
    var var_en_do: string; 
    var_en_do = "holi";
    print (var_en_do);
} while ((a == b) || (c != 15) && (a < 30));


for (let i: integer = 0; i < 3; i = i + 1) {
  print("Loop index: "+ i);  
  let en_for:string; 
  en_for = "Loop index: "+ i;
}

let numeros: integer[];
numeros = [1, 2, 3, 4, 5];  

foreach (item in numeros) {
  print(item);
}