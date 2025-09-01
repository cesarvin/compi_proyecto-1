import sys
from antlr4 import *
from visitor.CompiscriptLexer import CompiscriptLexer
from visitor.CompiscriptParser import CompiscriptParser
from cs_type_check_visitor import TypeCheckVisitor
from cs_init_visitor import InitVisitor
from recursos.error_handler import SyntaxErrorHandler, ErrorHandler
from recursos.symbol_table import SymbolTable
from recursos.type_table import TypeTable


def main(argv):
    
    input_stream = FileStream(argv[1], encoding="utf-8")
    
    compilado, result , errores, symbol_table, type_table = compilar(input_stream)
    
    if not compilado and result == 'Errores lexicos':
        print("\nSe encontraron errores de sintaxis:\n")
        for i, err in enumerate(errores, 1):
             print(f"  {i}. {err}")
    elif not compilado and result == 'Errores Semanticos':
         print("\nSe encontraron errores de semántica:\n")
         for i, err in enumerate(errores, 1):
             print(f"  {i}. {err}")
    


def compilar(code = ""):
    
    lexer = CompiscriptLexer(code)
    parser_listener = SyntaxErrorHandler()
    lexer_listener  = parser_listener

    lexer.removeErrorListeners()
    lexer.addErrorListener(lexer_listener)

    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)
    
    parser.removeErrorListeners()
    parser.addErrorListener(parser_listener)
    
    tree = parser.program()  

    handler = ErrorHandler()
    type_table = TypeTable()
    symbol_table = SymbolTable()

    if parser_listener.has_errors:
        
        for i, err in enumerate(parser_listener.errors, 1):
            off = f" — cerca de '{err['offending']}'" if err.get("offending") else ""
            message = (f"{err['message']}{off}")
            handler.add_error(message, err['line'], err['column'])

        return False, 'Errores lexicos', handler.to_dict(), None, None

    # primer visitor para determinar tipos y funciones
    init_visitor = InitVisitor(error_handler=handler, symbol_table=symbol_table, type_table=type_table)

    # try:
    init_visitor.visit(tree)

    if handler.has_errors():
        return False, 'Errores Semanticos', handler.to_dict() , None, None
    
    visitor = TypeCheckVisitor(error_handler=handler, symbol_table=symbol_table, type_table=type_table)

    # segundo visitor para analisis de tipos
    visitor.visit(tree)

    if handler.has_errors():
        return False, 'Errores Semanticos', handler.to_dict(), None, None
    
    # symbol_table.print_table()
    
    # type_table.print_table()
    
    return True, "El código está correcto", [], symbol_table.to_dict(), type_table.to_dict()
        
    # except OperationalError as e:
    #     return False, e


if __name__ == '__main__':
    #main(sys.argv)
    try:
        main(sys.argv)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)