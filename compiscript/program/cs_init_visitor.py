from visitor.CompiscriptParser import CompiscriptParser
from visitor.CompiscriptVisitor import CompiscriptVisitor
from recursos.custom_types import *
from recursos.error_handler import ErrorHandler
from recursos.symbol_table import *
from recursos.type_table import *


class InitVisitor(CompiscriptVisitor):
    def __init__(self, error_handler: ErrorHandler, symbol_table: SymbolTable, type_table: TypeTable):
        self.error_handler = error_handler
        self.symbol_table = symbol_table
        self.type_table = type_table

    def visitProgram(self, ctx:CompiscriptParser.ProgramContext):
        return self.visitChildren(ctx)

    
    def visitFunctionDeclaration(self, ctx:CompiscriptParser.FunctionDeclarationContext):
        return None
        

    def visitType(self, ctx:CompiscriptParser.TypeContext):
        
        base_type_name = ctx.baseType().getText()
        base_type_row = self.type_table.find(base_type_name)
        
        if not base_type_row:
            message = f"El tipo base '{base_type_name}' no está definido."
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
            return ErrorType()
        
        final_type = base_type_row.data_type
        
        if len(ctx.children) > 1:
            num_dimensions = (len(ctx.children) - 1) // 2
            for nd in range(num_dimensions):
                final_type = ArrayType(final_type)
        
        return final_type

    
    def visitClassDeclaration(self, ctx:CompiscriptParser.ClassDeclarationContext):
        
        clase = ctx.Identifier(0).getText()
    
        if self.type_table.find(clase):
            message = f"La clase '{clase}' ya está definida."
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
            return

        parent_name = "Object"
        attributes = {}
        prop_offset_counter = 0

        if len(ctx.Identifier()) > 1:
            parent_name = ctx.Identifier(1).getText() 
            parent_type =  self.type_table.find(parent_name)

            if not parent_type or not isinstance(parent_type.data_type, ClassType):
                message = f"La clase padre '{parent_name}' no existe o no es una clase."
                self.error_handler.add_error(message, ctx.Identifier(1).getSymbol().line, ctx.Identifier(1).getSymbol().column)
            elif parent_type.attributes:
                attributes = parent_type.attributes.copy()

        for member_ctx in ctx.classMember():
            if member_ctx.functionDeclaration():  
                method_decl = member_ctx.functionDeclaration()
                method_name = method_decl.Identifier().getText() 
                
                if method_name in attributes and clase ==  parent_name: 
                    self.error_handler.add_error(...)
                    continue
                
                param_types = []
                if method_decl.parameters():
                    for param_ctx in method_decl.parameters().parameter():
                        param_types.append(self.visit(param_ctx.type_())) 
                
                if method_name == "constructor":
                    return_type = ClassType(clase)   
                else:
                    return_type = self.type_table.find("nil").data_type 
                    if method_decl.type_():
                        return_type = self.visit(method_decl.type_())
                
                attributes[method_name] = FunctionType(return_type, param_types)

            elif member_ctx.variableDeclaration():
                prop_decl = member_ctx.variableDeclaration()
                prop_name = prop_decl.Identifier().getText()
                prop_type = self.visit(prop_decl.typeAnnotation().type_())
                attributes[prop_name] = {
                    'type': prop_type,
                    'offset': prop_offset_counter
                }
                
                type_row = self.type_table.find("array" if isinstance(prop_type, ArrayType) else str(prop_type))
                if type_row:
                    prop_offset_counter += type_row.size

        class_type_row = TypeRow(
            data_type=ClassType(clase), 
            size=8, 
            inherits=parent_name,  
            attributes=attributes
        )
        self.type_table.add(class_type_row)

        return None