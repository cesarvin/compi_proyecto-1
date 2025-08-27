import unittest
from antlr4 import InputStream 
from Driver import compilar

class TestCompilador(unittest.TestCase):

    def test_literales(self):
        codigo = '''
        123;          // integer
        "texto";      // string
        true; false;  // boolean
        null;         // nulo
        '''

        input_stream = InputStream(codigo)

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)


    def test_tipos_de_datos(self):
        codigo = '''
        let a: integer = 10;
        let b: string = "hola";
        let c: boolean = true;
        let d = null;
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)
    
    def test_constantes(self):
        codigo = '''
        const PI: integer = 314;
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)

if __name__ == '__main__':
    unittest.main()