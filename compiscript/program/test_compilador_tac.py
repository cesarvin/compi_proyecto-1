import unittest
from antlr4 import InputStream 
from Driver import compilar

class TestCompilador(unittest.TestCase):

    def test_case1(self):
        codigo = '''let a: integer;
a = 2* 8;
let x = a + 5;

print(x + 5);'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': '*', 'arg1': '2', 'arg2': '8', 'result': 't0'}, {'op': '=', 'arg1': 't0', 'arg2': None, 'result': '[BP+0]'}, {'op': '+', 'arg1': '[BP+0]', 'arg2': '5', 'result': 't1'}, {'op': '=', 'arg1': 't1', 'arg2': None, 'result': '[BP+8]'}, {'op': '+', 'arg1': '[BP+8]', 'arg2': '5', 'result': 't2'}, {'op': 'PARAM', 'arg1': 't2', 'arg2': None, 'result': None}, {'op': 'CALL', 'arg1': 'print', 'arg2': '1', 'result': None}]
        
        self.assertEqual(tac_code, esperado)

    def test_case2(self):
        codigo = '''let a: integer;
a = 2* 8;
let x = a + 5;

print(x + 5);

if (a > 10) {
  x = 1;
} else {
  x = 2;
}'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': '*', 'arg1': '2', 'arg2': '8', 'result': 't0'}, {'op': '=', 'arg1': 't0', 'arg2': None, 'result': '[BP+0]'}, {'op': '+', 'arg1': '[BP+0]', 'arg2': '5', 'result': 't1'}, {'op': '=', 'arg1': 't1', 'arg2': None, 'result': '[BP+8]'}, {'op': '+', 'arg1': '[BP+8]', 'arg2': '5', 'result': 't2'}, {'op': 'PARAM', 'arg1': 't2', 'arg2': None, 'result': None}, {'op': 'CALL', 'arg1': 'print', 'arg2': '1', 'result': None}, {'op': '>', 'arg1': '[BP+0]', 'arg2': '10', 'result': 't3'}, {'op': 'IF_FALSE', 'arg1': 't3', 'arg2': None, 'result': '_L0'}, {'op': '=', 'arg1': '1', 'arg2': None, 'result': '[BP+8]'}, {'op': 'GOTO', 'arg1': None, 'arg2': None, 'result': '_L1'}, {'op': '_L0:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '=', 'arg1': '2', 'arg2': None, 'result': '[BP+8]'}, {'op': '_L1:', 'arg1': None, 'arg2': None, 'result': None}]
        
        self.assertEqual(tac_code, esperado)

    def test_case3(self):
        codigo = '''let i = 0;
while (i < 2) {
  i = i + 1;
  
  print(i);
}'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': '=', 'arg1': '0', 'arg2': None, 'result': '[BP+0]'}, {'op': '_L0:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '<', 'arg1': '[BP+0]', 'arg2': '2', 'result': 't0'}, {'op': 'IF_FALSE', 'arg1': 't0', 'arg2': None, 'result': '_L1'}, {'op': '+', 'arg1': '[BP+0]', 'arg2': '1', 'result': 't1'}, {'op': '=', 'arg1': 't1', 'arg2': None, 'result': '[BP+0]'}, {'op': 'PARAM', 'arg1': '[BP+0]', 'arg2': None, 'result': None}, {'op': 'CALL', 'arg1': 'print', 'arg2': '1', 'result': None}, {'op': 'GOTO', 'arg1': None, 'arg2': None, 'result': '_L0'}, {'op': '_L1:', 'arg1': None, 'arg2': None, 'result': None}]
        
        self.assertEqual(tac_code, esperado)

    
    def test_case4(self):
        codigo = '''let i = 0;
do {
  i = i + 1;
} while (i < 3);

for (let i = 0; i < 2; i = i + 1) {
  print(i);
}'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': '=', 'arg1': '0', 'arg2': None, 'result': '[BP+0]'}, {'op': '_L0:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '+', 'arg1': '[BP+0]', 'arg2': '1', 'result': 't0'}, {'op': '=', 'arg1': 't0', 'arg2': None, 'result': '[BP+0]'}, {'op': '_L2:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '<', 'arg1': '[BP+0]', 'arg2': '3', 'result': 't1'}, {'op': 'IF_TRUE', 'arg1': 't1', 'arg2': None, 'result': '_L0'}, {'op': '_L1:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '=', 'arg1': '0', 'arg2': None, 'result': '[BP+0]'}, {'op': '_L3:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '<', 'arg1': '[BP+0]', 'arg2': '2', 'result': 't2'}, {'op': 'IF_FALSE', 'arg1': 't2', 'arg2': None, 'result': '_L5'}, {'op': 'PARAM', 'arg1': '[BP+0]', 'arg2': None, 'result': None}, {'op': 'CALL', 'arg1': 'print', 'arg2': '1', 'result': None}, {'op': '_L4:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '+', 'arg1': '[BP+0]', 'arg2': '1', 'result': 't3'}, {'op': '=', 'arg1': 't3', 'arg2': None, 'result': '[BP+0]'}, {'op': 'GOTO', 'arg1': None, 'arg2': None, 'result': '_L3'}, {'op': '_L5:', 'arg1': None, 'arg2': None, 'result': None}]
        
        self.assertEqual(tac_code, esperado)



    def test_case5(self):
        codigo = '''function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': 'factorial:', 'arg1': None, 'arg2': None, 'result': None}, {'op': 'BEGIN_FUNC', 'arg1': None, 'arg2': None, 'result': None}, {'op': '<=', 'arg1': '[BP+0]', 'arg2': '1', 'result': 't0'}, {'op': 'IF_FALSE', 'arg1': 't0', 'arg2': None, 'result': '_L1'}, {'op': 'RETURN', 'arg1': '1', 'arg2': None, 'result': None}, {'op': '_L1:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '-', 'arg1': '[BP+0]', 'arg2': '1', 'result': 't1'}, {'op': 'PARAM', 'arg1': 't1', 'arg2': None, 'result': None}, {'op': 'CALL', 'arg1': 'factorial', 'arg2': '1', 'result': 't2'}, {'op': '*', 'arg1': '[BP+0]', 'arg2': 't2', 'result': 't3'}, {'op': 'RETURN', 'arg1': 't3', 'arg2': None, 'result': None}, {'op': 'END_FUNC', 'arg1': None, 'arg2': None, 'result': None}]
        
        self.assertEqual(tac_code, esperado)




    def test_case6(self):
        codigo = '''class Dog {
  let name: string;

  function constructor(name: string) {
    this.name = name;
  }

  function speak(): string {
    return this.name + " makes a sound.";
  }
}

let dog: Dog = new Dog("Rex");

let dog2: Dog = new Dog("snoopy");'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': 'constructor:', 'arg1': None, 'arg2': None, 'result': None}, {'op': 'BEGIN_FUNC', 'arg1': None, 'arg2': None, 'result': None}, {'op': '=', 'arg1': 'this', 'arg2': None, 'result': 't0'}, {'op': '=', 'arg1': '[BP+0]', 'arg2': None, 'result': '[t0+0]'}, {'op': 'END_FUNC', 'arg1': None, 'arg2': None, 'result': None}, {'op': 'speak:', 'arg1': None, 'arg2': None, 'result': None}, {'op': 'BEGIN_FUNC', 'arg1': None, 'arg2': None, 'result': None}, {'op': '=', 'arg1': '[this+0]', 'arg2': None, 'result': 't1'}, {'op': '+', 'arg1': 't1', 'arg2': '" makes a sound."', 'result': 't2'}, {'op': 'RETURN', 'arg1': 't2', 'arg2': None, 'result': None}, {'op': 'END_FUNC', 'arg1': None, 'arg2': None, 'result': None}, {'op': 'PARAM', 'arg1': '"Rex"', 'arg2': None, 'result': None}, {'op': 'NEW', 'arg1': 'Dog', 'arg2': '1', 'result': 't3'}, {'op': '=', 'arg1': 't3', 'arg2': None, 'result': '[BP+8]'}, {'op': 'PARAM', 'arg1': '"snoopy"', 'arg2': None, 'result': None}, {'op': 'NEW', 'arg1': 'Dog', 'arg2': '1', 'result': 't4'}, {'op': '=', 'arg1': 't4', 'arg2': None, 'result': '[BP+16]'}]
        
        self.assertEqual(tac_code, esperado)

    
    
    def test_case7(self):
        codigo = '''let numbers: integer[] = [10, 20, 30];

foreach (num in numbers) {
  print(num);
}'''
        
        input_stream = InputStream(codigo)
        
        compilado, result , errores, symbol_table, type_table, tac_code = compilar(input_stream)
        
        esperado = [{'op': 'ALLOCATE', 'arg1': '24', 'arg2': None, 'result': 't0'}, {'op': '=', 'arg1': '10', 'arg2': None, 'result': '[t0+0]'}, {'op': '=', 'arg1': '20', 'arg2': None, 'result': '[t0+8]'}, {'op': '=', 'arg1': '30', 'arg2': None, 'result': '[t0+16]'}, {'op': '=', 'arg1': 't0', 'arg2': None, 'result': '[BP+0]'}, {'op': '=', 'arg1': '0', 'arg2': None, 'result': 't1'}, {'op': '_L0:', 'arg1': None, 'arg2': None, 'result': None}, {'op': '<', 'arg1': 't1', 'arg2': '3', 'result': 't2'}, {'op': 'IF_FALSE', 'arg1': 't2', 'arg2': None, 'result': '_L1'}, {'op': '*', 'arg1': 't1', 'arg2': '8', 'result': 't3'}, {'op': '+', 'arg1': '[BP+0]', 'arg2': 't3', 'result': 't4'}, {'op': '=', 'arg1': '[t4]', 'arg2': None, 'result': 't5'}, {'op': '=', 'arg1': 't5', 'arg2': None, 'result': '[BP+0]'}, {'op': 'PARAM', 'arg1': '[BP+0]', 'arg2': None, 'result': None}, {'op': 'CALL', 'arg1': 'print', 'arg2': '1', 'result': None}, {'op': '+', 'arg1': 't1', 'arg2': '1', 'result': 't6'}, {'op': '=', 'arg1': 't6', 'arg2': None, 'result': 't1'}, {'op': 'GOTO', 'arg1': None, 'arg2': None, 'result': '_L0'}, {'op': '_L1:', 'arg1': None, 'arg2': None, 'result': None}]
        
        self.assertEqual(tac_code, esperado)
    

if __name__ == '__main__':
    unittest.main()