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

    def test_asginacion_variables(self):
        codigo = '''
            let nombre: string;
            nombre = "Compiscript";
            
            let edad: integer;
            edad = 5;
            
            let esMujer: boolean;
            esMujer = true;

            let numeros: integer[];
            numeros = [1, 2, 3, 4, 5];  

            let colores: string[];
            colores = ["rojo", "verde", "azul"];
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)

    def test_asginacion_variables_error(self):
        codigo = '''
            let nombre: string;
            nombre = 1;
            
            let edad: integer;
            edad = "5";
            
            let esMujer: boolean;
            esMujer = "true";

            let numeros: integer[];
            numeros = [1, "2", 3, 4, 5];  

            let colores: string[];
            colores = ["rojo", 0, "azul"];
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, False)

    def test_operadores(self):
        codigo = '''
            let x:integer = 5 + 3 * 2;
            let y: boolean = !(x < 10 || x > 20);

            let a:integer = 10;
            let b:integer = 20;
            let c:integer = a + b * (a - b) / 2;
            let d: boolean = (a == b) || (c != 15) && (a < 30);
            let e: string = "hola" + "mundo";
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)
    
    def test_operadores_error(self):
        codigo = '''
            let x:integer = 5 + "3" * 2;
            let y: boolean = !("x" < 10 || x > 20);

            let a: integer = "diez";
            let d: boolean = 2 || (c != 15) && (a < 30);
            let c: string = "hola" + 5;
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, False)

        
    def test_bloques(self):
        codigo = '''
            let a: integer = 1;
            let b: integer = 2;
            let c: integer;

            c = a+b;

            {
                let d:integer;
                c = c+d;
            }
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)

    def test_ciclos(self):
        codigo = '''
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

                let xx: integer; 
                switch (xx) {
                case 1:
                    print("uno");
                case 2:
                    print("dos");
                default:
                    print("otro");
                }
        '''
        input_stream = InputStream(codigo)  

        compilado, msg ,errores = compilar(input_stream)

        self.assertEqual(compilado, True)

if __name__ == '__main__':
    unittest.main()