import sys
from antlr4 import *
from visitor.CompiscriptLexer import CompiscriptLexer
from visitor.CompiscriptParser import CompiscriptParser
from type_check_visitor import TypeCheckVisitor
from antlr4.error.ErrorListener import ErrorListener
from recursos.error_handler import ErrorHandler
from recursos.symbol_table import SymbolTable
from recursos.type_table import TypeTable

class CollectingErrorListener(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errors = []   # lista de dicts o strings

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # offendingSymbol puede ser None en errores del lexer
        text = getattr(offendingSymbol, "text", None)
        self.errors.append({
            "line": line,
            "column": column,
            "message": msg,
            "offending": text
        })

    @property
    def has_errors(self):
        return len(self.errors) > 0


def main(argv):
    
    input_stream = FileStream(argv[1], encoding="utf-8")
    
    compilado, msg ,errores = compilar(input_stream)
    
    if not compilado and msg == 'Errores lexicos':
        print("❌ Se encontraron errores de sintaxis:")
        for i, err in enumerate(errores, 1):
             print(f"  {i}. {err}")
    elif not compilado and msg == 'Errores Semanticos':
         print("❌ Se encontraron errores de semántica:")
         for i, err in enumerate(errores, 1):
             print(f"  {i}. {err}")
    else: 
         print("✅ Archivo correcto")


def compilar(code = ""):
    
    #try:
        lexer = CompiscriptLexer(code)
        parser_listener = CollectingErrorListener()
        lexer_listener  = parser_listener

        # Reemplazar listeners por defecto
        lexer.removeErrorListeners()
        lexer.addErrorListener(lexer_listener)

        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)
       
        parser.removeErrorListeners()
        parser.addErrorListener(parser_listener)
        
        tree = parser.program()  # We are using 'prog' since this is the starting rule based on our Compiscript grammar, yay!

        handler = ErrorHandler()
        type_table = TypeTable()
        symbol_table = SymbolTable(type_table)

        #valida que no hayan errores sintacticos antes de continuar.
        if parser_listener.has_errors:
            
            for i, err in enumerate(parser_listener.errors, 1):
                off = f" — cerca de '{err['offending']}'" if err.get("offending") else ""
                message = (f"{err['message']}{off}")
                handler.add_error(message, {err['line']}, {err['column']})

            return False, 'Errores lexicos', handler._errors

        visitor = TypeCheckVisitor(error_handler=handler, symbolTable=symbol_table, typeTable=type_table)

        try:
            visitor.visit(tree)

            if handler.has_errors():
                return False, 'Errores Semanticos', handler._errors
            
            symbol_table.print_table()
            print("Type checking passed - paso")
            
        except TypeError as e:
            print(f"Type checking error: {e}")

        return True, 'Type checking passed', ''
        
    # except OperationalError as e:
    #     return False, e


if __name__ == '__main__':
    # main(sys.argv)
    try:
        main(sys.argv)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)