from visitor.CompiscriptParser import CompiscriptParser
from visitor.CompiscriptVisitor import CompiscriptVisitor
from recursos.custom_types import *
from recursos.error_handler import ErrorHandler
from recursos.symbol_table import *
from recursos.type_table import *

class TypeCheckVisitor(CompiscriptVisitor):

    def __init__(self, error_handler: ErrorHandler, symbol_table: SymbolTable, type_table: TypeTable):

        super().__init__()
        self.error_handler = error_handler
        self.symbol_table = symbol_table
        self.type_table = type_table
        self.loops_count = 0
        self.switchs_count = 0
        self.current_function = None
        self.current_class = None 
        self.current_switch = []
        self.control_switch_cases = []

    # Visit a parse tree produced by CompiscriptParser#program.
    def visitProgram(self, ctx:CompiscriptParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#statement.
    def visitStatement(self, ctx:CompiscriptParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#block.
    def visitBlock(self, ctx:CompiscriptParser.BlockContext):
        # se crea un nuevo ambito  
        self.symbol_table.enter_scope()
        
        self.visitChildren(ctx)
        
        # self.symbol_table.print_table()
        # print("#" * 100 + "\n")
        # al finalzar se elimina el ambito
        #self.symbol_table.exit_scope()


    # Visit a parse tree produced by CompiscriptParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:CompiscriptParser.VariableDeclarationContext):
        
        ctx_variable = ctx.Identifier().getText()
        ctx_line = ctx.start.line   
        ctx_column = ctx.start.column   
        
        if self.symbol_table.find_in_current_scope(ctx_variable): 
            message = f"La variable '{ctx_variable}' ya ha sido declarada en este ámbito"
            self.error_handler.add_error(message, ctx_line, ctx_column) 
            return

        ctx_typeAnnotation = None
        if ctx.typeAnnotation():
            ctx_typeAnnotation = self.visit(ctx.typeAnnotation().type_())
            if isinstance(ctx_typeAnnotation, ErrorType):
                return 
        
        type_expression = None
        if ctx.initializer():
            type_expression = self.visit(ctx.initializer().expression()) 
            if isinstance(type_expression, ErrorType) or type_expression is None:
                return 

        tipo = None
        if ctx_typeAnnotation and type_expression: 
            if ctx_typeAnnotation != type_expression:   
                empty_array = (isinstance(type_expression, ArrayType) and isinstance(type_expression.element_type, ObjectType))  
                
                if not (isinstance(ctx_typeAnnotation, ArrayType) and empty_array):
                    message = f"Se intenta asignar un tipo '{type_expression}' a una variable de tipo '{ctx_typeAnnotation}'"
                    line = ctx.initializer().start.line  
                    column = ctx.initializer().start.column 
                    self.error_handler.add_error(message,  line, column)
                    return
            
            tipo = ctx_typeAnnotation
        elif ctx_typeAnnotation:
            tipo = ctx_typeAnnotation
        elif type_expression:
            tipo = type_expression
        else:
            message = f"La variable '{ctx_variable}' debe tener un tipo explícito"
            line = ctx.start.line
            column = ctx.start.column
            self.error_handler.add_error(message, line, column)
            return

        if tipo:
            type_name_for_lookup = ""
            if isinstance(tipo, ArrayType):
                type_name_for_lookup = "array" 
            else:
                type_name_for_lookup = str(tipo)

            type_row = self.type_table.find(type_name_for_lookup)
            if not type_row:
                message = f"Error interno: No se encontró el TypeRow para el tipo base '{type_name_for_lookup}'"
                line = ctx.start.line
                column = ctx.start.column
                self.error_handler.add_error(message, line, column)
                return

            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0

            new_symbol = VariableSymbol(
                id=ctx_variable,
                data_type=tipo, 
                size=type_row.size, 
                scope=scope_level,
                parent_scope=parent_level,
                p_class = self.current_class,
                p_function = self.current_function,
                role='Variable'
            )
            self.symbol_table.add(new_symbol)


    # Visit a parse tree produced by CompiscriptParser#constantDeclaration.
    def visitConstantDeclaration(self, ctx:CompiscriptParser.ConstantDeclarationContext):
        
        ctx_constante = ctx.Identifier().getText()
    
        if self.symbol_table.find_in_current_scope(ctx_constante):
            self.error_handler.add_error(f"El identificador '{ctx_constante}' ya ha sido declarada en este ámbito", ctx.start.line, ctx.start.column)
            return

        ctx_expresion_type = self.visit(ctx.expression())
        if not ctx_expresion_type or isinstance(ctx_expresion_type, ErrorType):
            return
            
        annotated_type = None
        if ctx.typeAnnotation():
            annotated_type = self.visit(ctx.typeAnnotation().type_())
            if isinstance(annotated_type, ErrorType):
                return

        final_type = None
        if annotated_type:
            if annotated_type != ctx_expresion_type:
                self.error_handler.add_error(f"No se puede asignar un valor de tipo '{ctx_expresion_type}' a una constante de tipo '{annotated_type}'", ctx.expression().start.line, ctx.expression().start.column)
                return
            final_type = annotated_type
        else:
            final_type = ctx_expresion_type

        if final_type:
            es_array = "array" if isinstance(final_type, ArrayType) else str(final_type)
            type_row = self.type_table.find(es_array)

            if not type_row:
                self.error_handler.add_error(f"Error interno: No se encontró el TypeRow para el tipo '{final_type}'", ctx.start.line, ctx.start.column)
                return

            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0

            new_symbol = VariableSymbol(
                id=ctx_constante,
                data_type=final_type,  
                size=type_row.size,
                scope=scope_level,
                parent_scope=parent_level,
                p_class = self.current_class,
                p_function = self.current_function,
                role='Constant'
            )
            self.symbol_table.add(new_symbol)
        


    # Visit a parse tree produced by CompiscriptParser#typeAnnotation.
    def visitTypeAnnotation(self, ctx:CompiscriptParser.TypeAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#initializer.
    def visitInitializer(self, ctx:CompiscriptParser.InitializerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#assignment.
    def visitAssignment(self, ctx:CompiscriptParser.AssignmentContext):
        
        target_type = None
        assigned_type = None
        assigned_expression = None

        if ctx.getChild(1).getText() == '.':
            instancia = self.visit(ctx.expression(0))
            if not isinstance(instancia, ClassType):
                message = f"El tipo '{instancia}' no corresponde a una instancia de clase."
                self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
                return ErrorType()

           
            clase_type = self.type_table.find(str(instancia))
            propiedad = ctx.Identifier().getText()

            if not clase_type or propiedad not in clase_type.attributes:
                message = f"El tipo '{instancia}' no tiene una propiedad llamada '{propiedad}'"
                self.error_handler.add_error(message, ctx.Identifier().getSymbol().line, ctx.Identifier().getSymbol().column)
                return ErrorType()
            
            target_type = clase_type.attributes[propiedad]

            assigned_expression = ctx.expression(1)
            assigned_type = self.visit(assigned_expression)

        else:
            variable = ctx.Identifier().getText()
            symbol = self.symbol_table.find(variable)

            if not symbol:
                message = f"La variable '{variable}' no ha sido declarada."
                self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
                return
            
            if hasattr(symbol, 'role') and symbol.role == 'Constant':
                message  = f"No se puede reasignar un valor a la constante '{variable}'"
                self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
                return

            target_type = symbol.data_type
            assigned_expression = ctx.expression(0)
            assigned_type = self.visit(assigned_expression)

        if not assigned_type or isinstance(assigned_type, ErrorType):
            return

        if target_type != assigned_type:
            is_generic_empty_array = (isinstance(assigned_type, ArrayType) and 
                                    isinstance(assigned_type.element_type, ObjectType))
            
            if not (str(target_type).startswith("Array<") and is_generic_empty_array):
                message = f"No se puede asignar un valor de tipo '{assigned_type}' a una variable de tipo '{target_type}'"
                self.error_handler.add_error(message, assigned_expression.start.line, assigned_expression.start.column)

        return None
        
        

    # Visit a parse tree produced by CompiscriptParser#expressionStatement.
    def visitExpressionStatement(self, ctx:CompiscriptParser.ExpressionStatementContext):
        self.visitChildren(ctx)
        return None


    # Visit a parse tree produced by CompiscriptParser#printStatement.
    def visitPrintStatement(self, ctx:CompiscriptParser.PrintStatementContext):
        self.visitChildren(ctx)
        return None


    # Visit a parse tree produced by CompiscriptParser#ifStatement.
    def visitIfStatement(self, ctx:CompiscriptParser.IfStatementContext):
        
        ctx_expression = self.visit(ctx.expression())
        ctx_line = ctx.expression().start.line
        ctx_column = ctx.expression().start.column

        if not isinstance(ctx_expression, BoolType):
            if not isinstance(ctx_expression, ErrorType):
                message = f"La condición en la sentencia 'if' es '{ctx_expression}' y debe ser de tipo 'boolean'"
                self.error_handler.add_error(message, ctx_line, ctx_column)

        self.visit(ctx.block(0))

        if len(ctx.block()) > 1:
            self.visit(ctx.block(1))
        
        return None


    # Visit a parse tree produced by CompiscriptParser#whileStatement.
    def visitWhileStatement(self, ctx:CompiscriptParser.WhileStatementContext):
        
        ctx_expression = self.visit(ctx.expression())
        ctx_line = ctx.expression().start.line
        ctx_column = ctx.expression().start.column

        if not isinstance(ctx_expression, BoolType):
            if not isinstance(ctx_expression, ErrorType):
                message = f"La condición en el ciclo 'while' es '{ctx_expression}' y debe ser de tipo 'boolean'"
                self.error_handler.add_error(message, ctx_line, ctx_column)

        self.loops_count += 1
        self.visit(ctx.block())
        self.loops_count -= 1
        
        return None


    # Visit a parse tree produced by CompiscriptParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:CompiscriptParser.DoWhileStatementContext):
        
        self.loops_count += 1
        self.visit(ctx.block())
        self.loops_count -= 1

        ctx_expression = self.visit(ctx.expression())
        ctx_line = ctx.expression().start.line  
        ctx_column = ctx.expression().start.column

        if not isinstance(ctx_expression, BoolType):
            if not isinstance(ctx_expression, ErrorType):
                message = f"La condición de el ciclo 'do-while' es '{ctx_expression}' y debe ser de tipo 'boolean'"
                self.error_handler.add_error(message, ctx_line, ctx_column)

        return None


    # Visit a parse tree produced by CompiscriptParser#forStatement.
    def visitForStatement(self, ctx:CompiscriptParser.ForStatementContext):
        
        #para el ciclo for se crea un ambito dado que se pueden declarar variables desde la condición
        self.symbol_table.enter_scope()

        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        
        if ctx.expression(0):
            ctx_expresion_type = self.visit(ctx.expression(0))
            if not isinstance(ctx_expresion_type, BoolType):
                if not isinstance(ctx_expresion_type, ErrorType):
                    message = f"La condición del ciclo 'for' es '{ctx_expresion_type}' y  debe ser de tipo 'boolean'"
                    self.error_handler.add_error(
                        message,
                        ctx.expression(0).start.line,
                        ctx.expression(0).start.column
                    )

        if ctx.expression(1):
            self.visit(ctx.expression(1))

        self.loops_count += 1
        self.visit(ctx.block())
        self.loops_count -= 1

        self.symbol_table.exit_scope()
        
        return None


    # Visit a parse tree produced by CompiscriptParser#foreachStatement.
    def visitForeachStatement(self, ctx:CompiscriptParser.ForeachStatementContext):
        
        ctx_expression = self.visit(ctx.expression())
        ctx_line = ctx.expression().start.line
        ctx_column = ctx.expression().start.column

        if not isinstance(ctx_expression, ArrayType):
            if not isinstance(ctx_expression, ErrorType):
                message = f"El tipo a iterar es '{ctx_expression}' y solo se puede iterar sobre arrays"
                self.error_handler.add_error(message, ctx_line, ctx_column)
            
            self.visit(ctx.block())
            return None

        self.symbol_table.enter_scope()

        ctx_identifier = ctx.Identifier().getText()
        
        ctx_expression_type = ctx_expression.element_type 
        
        type_row = self.type_table.find(str(ctx_expression_type))
        if not type_row:
            message = f"Error interno: No se encontró el TypeRow para el tipo '{ctx_expression_type}'"
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
            self.symbol_table.exit_scope() 
            return None

        scope_level = self.symbol_table.get_current_scope_level()
        parent_level = scope_level - 1

        new_symbol = VariableSymbol(
            id=ctx_identifier,
            data_type=ctx_expression_type,
            size=type_row.size,
            scope=scope_level,
            parent_scope=parent_level,
            p_class = self.current_class,
            p_function = self.current_function,
            role='Variable'
        )
        self.symbol_table.add(new_symbol)

        self.loops_count += 1
        self.visit(ctx.block())
        self.loops_count -= 1

        self.symbol_table.exit_scope()
        
        return None


    # Visit a parse tree produced by CompiscriptParser#breakStatement.
    def visitBreakStatement(self, ctx:CompiscriptParser.BreakStatementContext):
        if self.loops_count == 0 and self.switchs_count == 0:
            message = "La sentencia 'break' solo puede aparecer dentro de un ciclo o un switch."
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
        return None


    # Visit a parse tree produced by CompiscriptParser#continueStatement.
    def visitContinueStatement(self, ctx:CompiscriptParser.ContinueStatementContext):
        if self.loops_count == 0:
            message = "La sentencia 'continue' solo puede aparecer dentro de un ciclo."
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
        return None


    # Visit a parse tree produced by CompiscriptParser#returnStatement.
    def visitReturnStatement(self, ctx:CompiscriptParser.ReturnStatementContext):
        

        if self.current_function is None:
            self.error_handler.add_error("La sentencia 'return' solo puede aparecer dentro de una función.", ctx.start.line, ctx.start.column)
            return

        returned_type_obj = self.visit(ctx.expression())
        if not returned_type_obj or isinstance(returned_type_obj, ErrorType):
            return

        expected_type = None
        func_info = self.current_function

        if isinstance(func_info, FunctionSymbol):
            expected_type = func_info.data_type.return_type
        elif isinstance(func_info, FunctionType):
            expected_type = func_info.return_type
        else:
            self.error_handler.add_error(f"Error interno: 'current_function' tiene un tipo desconocido.", ctx.start.line, ctx.start.column)
            return

        if str(returned_type_obj) != str(expected_type):
            message = f"La función es de tipo '{expected_type}' y el retorno de tipo '{returned_type_obj}'"
            self.error_handler.add_error(message, ctx.start.line,  ctx.start.column)
        


    # Visit a parse tree produced by CompiscriptParser#tryCatchStatement.
    def visitTryCatchStatement(self, ctx:CompiscriptParser.TryCatchStatementContext):
        
        self.visit(ctx.block(0))

        self.symbol_table.enter_scope()

        ctx_identifier = ctx.Identifier().getText()
        exception_type = self.type_table.find("exception")
        
        scope_level = self.symbol_table.get_current_scope_level()
        parent_level = scope_level - 1

        exception_symbol = VariableSymbol(
            id=ctx_identifier,
            data_type=exception_type.data_type,
            size=exception_type.size,
            scope=scope_level,
            parent_scope=parent_level,
            role='execption'
        )
        self.symbol_table.add(exception_symbol)

        self.visit(ctx.block(1))

        self.symbol_table.exit_scope()

        return None
        

    # Visit a parse tree produced by CompiscriptParser#switchStatement.
    def visitSwitchStatement(self, ctx:CompiscriptParser.SwitchStatementContext):
        ctx_expression = self.visit(ctx.expression())
        
        if isinstance(ctx_expression, ErrorType):
            return 

        self.switchs_count += 1
        self.current_switch.append(ctx_expression)
        self.control_switch_cases.append(set())

        if ctx.switchCase():
            for case in ctx.switchCase():
                self.visit(case)
        
        if ctx.defaultCase():
            self.visit(ctx.defaultCase())

        self.control_switch_cases.pop()
        self.current_switch.pop()
        self.switchs_count -= 1
        return None
        


    # Visit a parse tree produced by CompiscriptParser#switchCase.
    def visitSwitchCase(self, ctx:CompiscriptParser.SwitchCaseContext):
        
        switch_type = self.current_switch[-1]
        casos = self.control_switch_cases[-1]

        case_expr_type = self.visit(ctx.expression())
        if isinstance(case_expr_type, ErrorType):
            return 

        if case_expr_type != switch_type:
            message = f"El tipo del 'case' ({case_expr_type}) no coincide con el tipo de la expresión del 'switch' ({switch_type})."
            self.error_handler.add_error(message, ctx.expression().start.line, ctx.expression().start.column)

        case_value = ctx.expression().getText()
        if case_value in casos:
            message = f"Valor de 'case' duplicado: {case_value}."
            self.error_handler.add_error(message, ctx.expression().start.line, ctx.expression().start.column)
        else:
            casos.add(case_value)

        for stmt_ctx in ctx.statement():
            self.visit(stmt_ctx)


    # Visit a parse tree produced by CompiscriptParser#defaultCase.
    def visitDefaultCase(self, ctx:CompiscriptParser.DefaultCaseContext):
        
        for stmt_ctx in ctx.statement():
            self.visit(stmt_ctx)


    # Visit a parse tree produced by CompiscriptParser#functionDeclaration.
    def visitFunctionDeclaration(self, ctx:CompiscriptParser.FunctionDeclarationContext):
        funcion = ctx.Identifier().getText()

        symbol = self.symbol_table.find_in_current_scope(funcion)

        if not symbol:
            params_types = []
            if ctx.parameters():
                for param_ctx in ctx.parameters().parameter():
                    param_type = self.visit(param_ctx.type_())
                    if isinstance(param_type, ErrorType): return
                    params_types.append(param_type)

            return_type = self.type_table.find("nil").data_type
            if ctx.type_():
                return_type = self.visit(ctx.type_())

            func_type_obj = FunctionType(return_type, params_types)
            
            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0
            
            symbol = FunctionSymbol(
                id=funcion,
                function_type_obj=func_type_obj,
                scope=scope_level,
                parent_scope=parent_level
            )
            
            if not self.symbol_table.add(symbol):
                message = f"La función '{funcion}' ya fue declarada en este ámbito"
                self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
                return

        previous_function = self.current_function
        self.current_function = symbol.data_type
        
        self.symbol_table.enter_scope()
        
        if ctx.parameters():
            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1

            for i, param_ctx in enumerate(ctx.parameters().parameter()):
                param_name = param_ctx.Identifier().getText()
                param_type = symbol.data_type.param_types[i]
                type_row = self.type_table.find(str(param_type))

                param_symbol = VariableSymbol(
                    id=param_name, data_type=param_type,
                    size=type_row.size if type_row else 0,
                    scope=scope_level, 
                    parent_scope=parent_level, 
                    p_class = self.current_class,
                    p_function = funcion,
                    role='Parameter'
                )
                self.symbol_table.add(param_symbol)

        self.visit(ctx.block())
        
        self.symbol_table.exit_scope()
        self.current_function = previous_function

        return None

        
        

    # Visit a parse tree produced by CompiscriptParser#parameters.
    def visitParameters(self, ctx:CompiscriptParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameter.
    def visitParameter(self, ctx:CompiscriptParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classDeclaration.
    def visitClassDeclaration(self, ctx:CompiscriptParser.ClassDeclarationContext):
        clase = ctx.Identifier(0).getText()
        clase_typo = self.type_table.find(clase)

        if not clase_typo:
            return

        previous_class = self.current_class
        self.current_class = clase_typo.data_type

        self.symbol_table.enter_scope()

        scope_level = self.symbol_table.get_current_scope_level()
        parent_level = scope_level - 1
        
        if clase_typo.attributes:
            for name, member_type in clase_typo.attributes.items():
                if isinstance(member_type, FunctionType):
                    method_symbol = FunctionSymbol(
                        id=name,
                        function_type_obj=member_type,
                        scope=scope_level,
                        parent_scope=parent_level
                    )
                    self.symbol_table.add(method_symbol)

        
        for member in ctx.classMember():
            if member.functionDeclaration(): 
                self.visit(member)
        
        
        self.symbol_table.exit_scope()
        
        self.current_class = previous_class
        
        return None
        
      

    # Visit a parse tree produced by CompiscriptParser#classMember.
    def visitClassMember(self, ctx:CompiscriptParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#expression.
    def visitExpression(self, ctx:CompiscriptParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#AssignExpr.
    def visitAssignExpr(self, ctx:CompiscriptParser.AssignExprContext):
        
        assigned_type = self.visit(ctx.assignmentExpr())
        if not assigned_type or isinstance(assigned_type, ErrorType):
            return ErrorType()

        target_type = self.visit(ctx.lhs)
        if not target_type or isinstance(target_type, ErrorType):
            return ErrorType()

        symbol = self.symbol_table.find(ctx.lhs.getText())
        if symbol and hasattr(symbol, 'role') and symbol.role == 'Constant':
            message = f"No se puede reasignar un valor a la constante '{symbol.id}'"
            self.error_handler.add_error(message, ctx.lhs.start.line, ctx.lhs.start.column)
            return ErrorType()

        if target_type != assigned_type:
            message = f"No se puede asignar un valor de tipo '{assigned_type}' a un destino de tipo '{target_type}'"
            self.error_handler.add_error(message, ctx.assignmentExpr().start.line, ctx.assignmentExpr().start.column)
            return ErrorType()
            
        return assigned_type
        
        


    # Visit a parse tree produced by CompiscriptParser#PropertyAssignExpr.
    def visitPropertyAssignExpr(self, ctx:CompiscriptParser.PropertyAssignExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ExprNoAssign.
    def visitExprNoAssign(self, ctx:CompiscriptParser.ExprNoAssignContext):
        return self.visit(ctx.conditionalExpr())


    # Visit a parse tree produced by CompiscriptParser#TernaryExpr.
    def visitTernaryExpr(self, ctx:CompiscriptParser.TernaryExprContext):
        
        if len(ctx.children) == 1:
            return self.visit(ctx.logicalOrExpr())

        logical_or_expr_type = self.visit(ctx.logicalOrExpr())
        
        if not isinstance(logical_or_expr_type, BoolType):
            if not isinstance(logical_or_expr_type, ErrorType):
                message = f"La condición del operador ? debe ser de tipo 'boolean', se encontró '{logical_or_expr_type}'"
                line = ctx.logicalOrExpr().start.line
                column = ctx.logicalOrExpr().start.column
                self.error_handler.add_error(message, line, column)
            return ErrorType()

        true_out_type = self.visit(ctx.expression(0))
        false_out_type = self.visit(ctx.expression(1))

        if isinstance(true_out_type, ErrorType) or isinstance(false_out_type, ErrorType):
            return ErrorType()
            
        if true_out_type != false_out_type:
            message = f"Las salidas del operador ? deben tener el mismo tipo, pero se encontraron '{true_out_type}' y '{false_out_type}'"
            line = ctx.expression(0).start.line
            column = ctx.expression(0).start.column
            self.error_handler.add_error(message, line, column)
            return ErrorType()

        return true_out_type


    # Visit a parse tree produced by CompiscriptParser#logicalOrExpr.
    def visitLogicalOrExpr(self, ctx:CompiscriptParser.LogicalOrExprContext):
        operands = ctx.logicalAndExpr()
        if len(operands) == 1:
            return self.visit(operands[0])

        left_type = self.visit(operands[0])
        right_type = self.visit(operands[1])
        
        op_token = ctx.getChild(1).getSymbol()

        if isinstance(left_type, BoolType) and isinstance(right_type, BoolType):
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"El operador lógico '{op_token.text}' solo se aplica a operadores 'boolean', no entre '{left_type}' y '{right_type}'"
        self.error_handler.add_error(message, op_token.line, op_token.column)
        return ErrorType()
        


    # Visit a parse tree produced by CompiscriptParser#logicalAndExpr.
    def visitLogicalAndExpr(self, ctx:CompiscriptParser.LogicalAndExprContext):
        operands = ctx.equalityExpr()
        if len(operands) == 1:
            return self.visit(operands[0])

        left_type = self.visit(operands[0])
        right_type = self.visit(operands[1])
        
        op_token = ctx.getChild(1).getSymbol()

        if isinstance(left_type, BoolType) and isinstance(right_type, BoolType):
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"El operador lógico '{op_token.text}' solo se aplica a operadores 'boolean', no entre '{left_type}' y '{right_type}'"
        self.error_handler.add_error(message, op_token.line, op_token.column)
        return ErrorType()
        


    # Visit a parse tree produced by CompiscriptParser#equalityExpr.
    def visitEqualityExpr(self, ctx:CompiscriptParser.EqualityExprContext):
        operands = ctx.relationalExpr()
        if len(operands) == 1:
            return self.visit(operands[0])

        left_type = self.visit(operands[0])
        right_type = self.visit(operands[1])
        
        op_token = ctx.getChild(1).getSymbol()

        equalily_types = False
        
        if isinstance(left_type, IntType) and isinstance(right_type, IntType):
            equalily_types = True
        elif isinstance(left_type, StringType) and isinstance(right_type, StringType):
            equalily_types = True
        elif isinstance(left_type, BoolType) and isinstance(right_type, BoolType):
            equalily_types = True
        
        if equalily_types:
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"La comparación de igualdad '{op_token.text}' no se puede realizar entre '{left_type}' y '{right_type}'"
        self.error_handler.add_error(message, op_token.line, op_token.column)
        return ErrorType()
        


    # Visit a parse tree produced by CompiscriptParser#relationalExpr.
    def visitRelationalExpr(self, ctx:CompiscriptParser.RelationalExprContext):
        operands = ctx.additiveExpr()
        if len(operands) == 1:
            return self.visit(operands[0])

        left_type = self.visit(operands[0])
        right_type = self.visit(operands[1])
        
        op_token = ctx.getChild(1).getSymbol()

        if isinstance(left_type, IntType) and isinstance(right_type, IntType):
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"Las comparaciones '{op_token.text}' no se pueden realizar entre '{left_type}' y '{right_type}'"
        self.error_handler.add_error(message, op_token.line, op_token.column)
        return ErrorType()
       


    # Visit a parse tree produced by CompiscriptParser#additiveExpr.
    def visitAdditiveExpr(self, ctx:CompiscriptParser.AdditiveExprContext):
        
        ops = ctx.multiplicativeExpr()
        
        if len(ops) == 1:
            result = self.visit(ops[0])
            return result

        current_type = self.visit(ops[0])
        
        for i in range(1, len(ops)):
            if current_type is None:
                return None

            right_type = self.visit(ops[i])
            op_node = ctx.children[2 * i - 1]
            op_token = op_node.getSymbol()

            previous_type = current_type
            
            current_type = None

            if isinstance(previous_type, IntType) and isinstance(right_type, IntType):
                current_type = IntType()
        
            elif op_token.text == '+' and isinstance(previous_type, StringType) and isinstance(right_type, StringType):
                current_type = StringType()

            elif op_token.text == '+' and isinstance(previous_type, StringType) and isinstance(right_type, IntType):
                current_type = StringType()

            elif op_token.text == '+' and isinstance(previous_type, IntType) and isinstance(right_type, StringType):
                current_type = StringType()
            
            elif op_token.text == '+' and isinstance(previous_type, ExceptionType) and isinstance(right_type, StringType):
                current_type = StringType()
            
            elif op_token.text == '+' and isinstance(previous_type, StringType) and isinstance(right_type, ExceptionType):
                current_type = StringType()
            else:
            
                message = f"La operación '{op_token.text}' no se puede aplicar a operandos de distintos tipos: '{previous_type}' y '{right_type}'"
                line = op_token.line
                column = op_token.column
                self.error_handler.add_error(message, line, column)
                current_type = ErrorType()
            
        
        return current_type


    # Visit a parse tree produced by CompiscriptParser#multiplicativeExpr.
    def visitMultiplicativeExpr(self, ctx:CompiscriptParser.MultiplicativeExprContext):
         
        operands = ctx.unaryExpr()
        
        if len(operands) == 1:
            return self.visit(operands[0])

        current_type = self.visit(operands[0])

        for i in range(1, len(operands)):
            if current_type is None:
                return None 

            right_type = self.visit(operands[i])
            op_node = ctx.children[2 * i - 1]
            op_token = op_node.getSymbol()

            previous_type = current_type
            current_type = None

            if isinstance(previous_type, IntType) and isinstance(right_type, IntType):
                current_type = IntType()
            
            if current_type is None:
                message = f"La operación '{op_token.text}' solo se puede aplicar a operandos de tipo 'integer' y se intentan operar '{previous_type}' y '{right_type}'"
                line = op_token.line
                column = op_token.column
                self.error_handler.add_error(message, line, column)
                return None

        return current_type


    # Visit a parse tree produced by CompiscriptParser#unaryExpr.
    def visitUnaryExpr(self, ctx:CompiscriptParser.UnaryExprContext):
        
        if ctx.primaryExpr():
            return self.visit(ctx.primaryExpr())

        unary_expr_type = self.visit(ctx.unaryExpr())
        
        if isinstance(unary_expr_type, ErrorType):
            return ErrorType()

        op_node = ctx.children[0]
        op_token = op_node.getSymbol()
        line = op_token.line
        column = op_token.column

        if op_token.text == '-':
            if isinstance(unary_expr_type, IntType):
                return IntType()
            else:
                message = f"El operador de negación '-' solo se puede aplicar a operandos de tipo 'integer', no a '{unary_expr_type}'"
                self.error_handler.add_error(message, line, column)
                return ErrorType()

        elif op_token.text == '!':
            if isinstance(unary_expr_type, BoolType):
                return BoolType()
            else:
                message = f"El operador lógico '!' solo se puede aplicar a operandos de tipo 'boolean', no a '{unary_expr_type}'"
                self.error_handler.add_error(message, line, column)
                return ErrorType()

        return ErrorType()


    # Visit a parse tree produced by CompiscriptParser#primaryExpr.
    def visitPrimaryExpr(self, ctx:CompiscriptParser.PrimaryExprContext):
        
        if ctx.expression():
            return self.visit(ctx.expression())
        elif ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        elif ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        return ErrorType()


    # Visit a parse tree produced by CompiscriptParser#literalExpr.
    def visitLiteralExpr(self, ctx:CompiscriptParser.LiteralExprContext):

        ctx_literal = ctx.getText()
        
        if ctx_literal=="true" or ctx_literal=="false":
            return BoolType()
        
        elif ctx_literal=="null":
            return ObjectType()
       
        elif ctx.literal():
            ctx_literal = ctx.literal()
            
            if ctx_literal.IntegerLiteral():
                return IntType()
            elif ctx_literal.StringLiteral():
                return StringType()

        elif ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        
        return None


    # Visit a parse tree produced by CompiscriptParser#leftHandSide.
    def visitLeftHandSide(self, ctx:CompiscriptParser.LeftHandSideContext):
        
        current_type = self.visit(ctx.primaryAtom())

        for suffix in ctx.suffixOp():
            if isinstance(current_type, ErrorType):
                return ErrorType()

            if isinstance(suffix, CompiscriptParser.IndexExprContext): 
                if not isinstance(current_type, ArrayType):
                    message = f"Solo se puede acceder por índice a los arrays y no '{current_type}'"
                    self.error_handler.add_error(message, suffix.start.line, suffix.start.column)
                    return ErrorType()

                index_type = self.visit(suffix.expression())
                if not isinstance(index_type, IntType):
                    message = f"El índice de un array debe ser de tipo 'integer' y no '{index_type}'"
                    self.error_handler.add_error(message, suffix.expression().start.line, suffix.expression().start.column)
                    return ErrorType()
                
                current_type = current_type.element_type
            
            elif isinstance(suffix, CompiscriptParser.CallExprContext):
                if not isinstance(current_type, FunctionType):
                    message = f"El tipo '{current_type}' no es una función y no se puede llamar"
                    self.error_handler.add_error(message, suffix.start.line, suffix.start.column)
                    return ErrorType()
        
                arg_expressions = []
                if suffix.arguments():
                    arg_expressions = suffix.arguments().expression()
                
                expected_param_count = len(current_type.param_types)
                provided_arg_count = len(arg_expressions)

                if expected_param_count != provided_arg_count:
                    message = f"La función esperaba {expected_param_count} argumentos, pero recibió {provided_arg_count}"
                    self.error_handler.add_error(message, suffix.start.line, suffix.start.column)
                    return ErrorType()

                for i, arg_expr in enumerate(arg_expressions):
                    arg_type = self.visit(arg_expr)
                    expected_param_type = current_type.param_types[i]
                    if arg_type != expected_param_type:
                        if not isinstance(arg_type, ErrorType):
                            message = f"El argumento {i+1} es de tipo incorrecto. Se esperaba '{expected_param_type}' pero se recibió '{arg_type}'"
                            self.error_handler.add_error(message, arg_expr.start.line, arg_expr.start.column)
                
                current_type = current_type.return_type
            
            elif isinstance(suffix, CompiscriptParser.PropertyAccessExprContext):
                if not isinstance(current_type, ClassType):
                    message = f"Solo se puede acceder a propiedades en una instancia de clase, no en el tipo '{current_type}'"
                    self.error_handler.add_error(message, suffix.start.line, suffix.start.column)
                    return ErrorType()

                clase = str(current_type)
                class_type_row = self.type_table.find(clase)
                prop_name = suffix.Identifier().getText()

                if prop_name not in class_type_row.attributes:
                    message = f"El tipo '{clase}' no tiene una propiedad llamada '{prop_name}'"
                    self.error_handler.add_error(message, suffix.start.line, suffix.start.column)
                    return ErrorType()
                
                current_type = class_type_row.attributes[prop_name]

        return current_type


    # Visit a parse tree produced by CompiscriptParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:CompiscriptParser.IdentifierExprContext):
        identificador = ctx.getText()
        symbol = self.symbol_table.find(identificador)
        
        if not symbol:
            message = f"La variable '{identificador}' no ha sido declarada."
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
            return ErrorType()

        return symbol.data_type
        


    # Visit a parse tree produced by CompiscriptParser#NewExpr.
    def visitNewExpr(self, ctx:CompiscriptParser.NewExprContext):
        
        clase = ctx.Identifier().getText()

        type_row = self.type_table.find(clase)

        if not type_row or not isinstance(type_row.data_type, ClassType):
            message = f"El tipo '{clase}' nno se puede instanciar porque no es una clase"
            self.error_handler.add_error(message,ctx.start.line, ctx.start.column)
            return ErrorType()

        constructor_signature = None

        if "constructor" in type_row.attributes:
            attr = type_row.attributes["constructor"]
            if isinstance(attr, FunctionType):
                constructor_signature = attr
        
        provided_arg_types = []
        arg_expressions = []

        if ctx.arguments():
            arg_expressions = ctx.arguments().expression()
            
            for arg_expr in arg_expressions:
                provided_arg_types.append(self.visit(arg_expr))

        if constructor_signature:
            
            expected_param_types = constructor_signature.param_types

            if len(expected_param_types) != len(provided_arg_types):
            
                message = f"El constructor de '{clase}' esperaba {len(expected_param_types)} argumentos y recibió {len(provided_arg_types)}"
                self.error_handler.add_error(message,ctx.start.line, ctx.start.column)
                return ErrorType()

            for i, arg_type in enumerate(provided_arg_types):
                expected_type = expected_param_types[i]
            
                if arg_type != expected_type and not isinstance(arg_type, ErrorType):
                    message = f"El argumento {i+1} del constructor es de tipo incorrecto. Se esperaba '{expected_type}' pero se recibió '{arg_type}'"
                    self.error_handler.add_error(message,arg_expressions[i].start.line, arg_expressions[i].start.column)
        
        elif len(provided_arg_types) > 0:
            message = f"La clase '{clase}' no tiene un constructor definido. Se proporcionaron {len(provided_arg_types)} argumentos invalidos"
            self.error_handler.add_error(message,ctx.start.line, ctx.start.column)
            return ErrorType()
             
        return type_row.data_type


    # Visit a parse tree produced by CompiscriptParser#ThisExpr.
    def visitThisExpr(self, ctx:CompiscriptParser.ThisExprContext):
        if self.current_class is None:
            message = "La palabra clave 'this' solo puede aparecer dentro de una clase"
            self.error_handler.add_error(message, ctx.start.line, ctx.start.column)
            return ErrorType()
        return self.current_class


    # Visit a parse tree produced by CompiscriptParser#CallExpr.
    def visitCallExpr(self, ctx:CompiscriptParser.CallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#IndexExpr.
    def visitIndexExpr(self, ctx:CompiscriptParser.IndexExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#PropertyAccessExpr.
    def visitPropertyAccessExpr(self, ctx:CompiscriptParser.PropertyAccessExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#arguments.
    def visitArguments(self, ctx:CompiscriptParser.ArgumentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#arrayLiteral.
    def visitArrayLiteral(self, ctx:CompiscriptParser.ArrayLiteralContext):
        ctx_expressions = ctx.expression()

        if not ctx_expressions:
            return ArrayType(ObjectType())

        first_expression_type = self.visit(ctx_expressions[0])
        
        for i in range(1, len(ctx_expressions)):
            current_expression_type = self.visit(ctx_expressions[i])

            if current_expression_type != first_expression_type:
                line = ctx_expressions[i].start.line
                column = ctx_expressions[i].start.column
                message = f"No se pueden mezclar tipos en un array. Se esperaba '{first_expression_type}' y se encontró '{current_expression_type}'"
                self.error_handler.add_error(message, line, column)
                return None 

        return ArrayType(first_expression_type)


    # Visit a parse tree produced by CompiscriptParser#type.
    def visitType(self, ctx:CompiscriptParser.TypeContext):
        
        base_type_name = ctx.baseType().getText()
        base_type_row = self.type_table.find(base_type_name)
        
        if not base_type_row:
            message = f"El tipo generico '{base_type_name}' no está definido"
            line = ctx.start.line
            column = ctx.start.column
            self.error_handler.add_error(message, line, column)
            return ErrorType()

        final_type = base_type_row.data_type

        if len(ctx.children) > 1:
            num_dimensions = (len(ctx.children) - 1) // 2
            for nd in range(num_dimensions):
                final_type = ArrayType(final_type)
                
        return final_type


    # Visit a parse tree produced by CompiscriptParser#baseType.
    def visitBaseType(self, ctx:CompiscriptParser.BaseTypeContext):
        return self.visitChildren(ctx)
