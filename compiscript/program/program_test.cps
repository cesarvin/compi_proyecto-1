
let numbers: integer[];
numbers = [1, 2, 3, 4, 5]; 

try {
  let risky: integer = numbers[10];
  print("Risky access: " + risky);
} catch (err) {
  print("Caught an error: " + err);
}
