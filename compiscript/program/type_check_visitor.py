from visitor.CompiscriptParser import CompiscriptParser
from visitor.CompiscriptVisitor import CompiscriptVisitor
from recursos.custom_types import IntType, StringType, BoolType, ObjectType, ArrayType, ErrorType
from recursos.error_handler import ErrorHandler
from recursos.symbol_table import *
from recursos.type_table import *

class TypeCheckVisitor(CompiscriptVisitor):

    def __init__(self, error_handler: ErrorHandler, symbolTable: SymbolTable, typeTable: TypeTable):

        super().__init__()
        self.error_handler = error_handler
        self.symbol_table = symbolTable
        self.type_table = typeTable

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
        
        # al finalzar se elimina el ambito
        self.symbol_table.exit_scope()


    # Visit a parse tree produced by CompiscriptParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:CompiscriptParser.VariableDeclarationContext):
        
        ctx_identifier = ctx.Identifier().getText()
        
        if self.symbol_table.find_in_current_scope(ctx_identifier):
            message = f"El identificador '{ctx_identifier}' ya ha sido declarado en este ámbito."
            line = ctx.start.line
            column = ctx.start.column            
            self.error_handler.add_error(message, line, column)
            return

        type_annotation = None
        if ctx.typeAnnotation():
            type_annotation = self.visit(ctx.typeAnnotation().type_())
            if isinstance(type_annotation, ErrorType):
                return # se sale si no es valido el tipo anotado
        
        type_expression = None
        if ctx.initializer():
            type_expression = self.visit(ctx.initializer().expression())
            if isinstance(type_expression, ErrorType) or type_expression is None:
                return # si la expresion tiene un error se sale

        data_type = None
        if type_annotation and type_expression:
            if type_annotation != type_expression:
                empty_array = (isinstance(type_expression, ArrayType) and isinstance(type_expression.element_type, ObjectType))
                
                if not (isinstance(type_annotation, ArrayType) and empty_array):
                    message = f"No se puede asignar un valor de tipo '{type_expression}' a una variable de tipo '{type_annotation}'."
                    line = ctx.initializer().start.line
                    column = ctx.initializer().start.column
                    self.error_handler.add_error(message, line, column)
                    return
            
            data_type = type_annotation
        elif type_annotation:
            data_type = type_annotation
        elif type_expression:
            data_type = type_expression
        else:
            message = f"La variable '{ctx_identifier}' debe tener un tipo explícito o un valor inicial."
            line = ctx.start.line
            column = ctx.start.column
            self.error_handler.add_error(message, line, column)
            return

        if data_type:
            type_name_for_lookup = ""
            if isinstance(data_type, ArrayType):
                type_name_for_lookup = "array" 
            else:
                type_name_for_lookup = str(data_type)

            type_row = self.type_table.find(type_name_for_lookup)
            if not type_row:
                message = f"Error interno: No se encontró el TypeRow para el tipo base '{type_name_for_lookup}'."
                line = ctx.start.line
                column = ctx.start.column
                self.error_handler.add_error(message, line, column)
                return

            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0

            new_symbol = SymbolRow(
                id=ctx_identifier,
                data_type=str(data_type), 
                size=type_row.size, 
                scope=scope_level,
                parent_scope=parent_level,
                is_param='Variable'
            )
            self.symbol_table.add(new_symbol)


    # Visit a parse tree produced by CompiscriptParser#constantDeclaration.
    def visitConstantDeclaration(self, ctx:CompiscriptParser.ConstantDeclarationContext):
        ctx_identifier = ctx.Identifier().getText()

        if self.symbol_table.find_in_current_scope(ctx_identifier):
            message = f"El identificador '{ctx_identifier}' ya ha sido declarado en este ámbito."
            line = ctx.start.line
            column = ctx.start.column
            self.error_handler.add_error(message, line, column)
            return

        type_annotation = None
        
        if ctx.typeAnnotation():
            type_name = ctx.typeAnnotation().type_().getText()
            type_annotation = self.type_table.find(type_name)
            if not type_annotation:
                message = f"El tipo '{type_name}' no está definido."
                line = ctx.typeAnnotation().start.line
                column = ctx.typeAnnotation().start.column
                self.error_handler.add_error(message, line, column)
                return

        expression_type = self.visit(ctx.expression())
        if not expression_type:
            return # Error al evaluar la expresión

        type_row = None
        if type_annotation:
            if str(type_annotation.data_type) != str(expression_type):
                message = f"No se puede asignar un valor de tipo '{expression_type}' a una constante de tipo '{type_annotation.data_type}'."
                line = ctx.expression().start.line
                column = ctx.expression().start.column
                self.error_handler.add_error(message, line, column)
                return
            type_row = type_annotation
        else:
            type_row = self.type_table.find(str(expression_type))

        if type_row:
            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0

            new_symbol = SymbolRow(
                id=ctx_identifier,
                data_type=str(type_row.data_type),
                size=type_row.size,
                scope=scope_level,
                parent_scope=parent_level,
                is_param='Constant' 
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
        
        if ctx.Identifier():
            ctx_identifier = ctx.Identifier().getText()
            
            symbol = self.symbol_table.find(ctx_identifier)

            if not symbol:
                message = f"Intento de asignar a una variable no declarada '{ctx_identifier}'."
                line = ctx.start.line
                column = ctx.start.column
                self.error_handler.add_error(message, line, column)
                return None

            if symbol.is_param == 'Constant':
                message = f"Intento de reasignar una constante '{ctx_identifier}'."
                line = ctx.start.line
                column = ctx.start.column
                self.error_handler.add_error(message, line, column)
                return None

            expected_type = symbol.data_type
            
            expression_type = self.visit(ctx.expression(0))
            if not expression_type:
                return None
            
            assigned_type_name = str(expression_type) 

            if expected_type != assigned_type_name:
                message = f"No se puede asignar un valor de tipo '{assigned_type_name}' a una variable de tipo '{expected_type}'."
                line = ctx.expression(0).start.line
                column = ctx.expression(0).start.column
                self.error_handler.add_error(message, line, column)
                return None
                
        # TODO asignación de propiedades objeto.prop = valor
        # elif ctx.expression() and len(ctx.expression()) > 1:
            # TODO...

        # Una asignación no tiene un tipo, por lo que no devolvemos nada
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

        if not isinstance(ctx_expression, BoolType):
            if not isinstance(ctx_expression, ErrorType):
                message = f"La condición de una sentencia 'if' debe ser de tipo 'boolean', no '{ctx_expression}'."
                line = ctx.expression().start.line
                column = ctx.expression().start.column
                self.error_handler.add_error(message, line, column)

        self.visit(ctx.block(0))

        if len(ctx.block()) > 1:
            self.visit(ctx.block(1))
        
        return None


    # Visit a parse tree produced by CompiscriptParser#whileStatement.
    def visitWhileStatement(self, ctx:CompiscriptParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:CompiscriptParser.DoWhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#forStatement.
    def visitForStatement(self, ctx:CompiscriptParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#foreachStatement.
    def visitForeachStatement(self, ctx:CompiscriptParser.ForeachStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#breakStatement.
    def visitBreakStatement(self, ctx:CompiscriptParser.BreakStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#continueStatement.
    def visitContinueStatement(self, ctx:CompiscriptParser.ContinueStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#returnStatement.
    def visitReturnStatement(self, ctx:CompiscriptParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#tryCatchStatement.
    def visitTryCatchStatement(self, ctx:CompiscriptParser.TryCatchStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#switchStatement.
    def visitSwitchStatement(self, ctx:CompiscriptParser.SwitchStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#switchCase.
    def visitSwitchCase(self, ctx:CompiscriptParser.SwitchCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#defaultCase.
    def visitDefaultCase(self, ctx:CompiscriptParser.DefaultCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#functionDeclaration.
    def visitFunctionDeclaration(self, ctx:CompiscriptParser.FunctionDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameters.
    def visitParameters(self, ctx:CompiscriptParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameter.
    def visitParameter(self, ctx:CompiscriptParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classDeclaration.
    def visitClassDeclaration(self, ctx:CompiscriptParser.ClassDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classMember.
    def visitClassMember(self, ctx:CompiscriptParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#expression.
    def visitExpression(self, ctx:CompiscriptParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#AssignExpr.
    def visitAssignExpr(self, ctx:CompiscriptParser.AssignExprContext):
        
        assignment_expr_type = self.visit(ctx.assignmentExpr())

        var_name = ctx.lhs.getText()
        symbol = self.symbol_table.find(var_name)
        
        if not symbol:
            message = f"Intento de asignar a una variable no declarada '{var_name}'."
            line = ctx.lhs.start.line
            column = ctx.lhs.start.column
            self.error_handler.add_error(message, line, column)
            return ErrorType()

        if symbol.is_param == 'Constant':
            message = f"No se puede reasignar un valor a la constante '{var_name}'."
            line = ctx.lhs.start.line
            column = ctx.lhs.start.column
            self.error_handler.add_error(message, line, column)
            return ErrorType()

        symbol_type_name = symbol.data_type
        assigned_type_name = str(assignment_expr_type.data_type if isinstance(assignment_expr_type, TypeRow) else assignment_expr_type)

        if symbol_type_name != assigned_type_name:
            message = f"No se puede asignar un valor de tipo '{assigned_type_name}' a una variable de tipo '{symbol_type_name}'."
            line = ctx.assignmentExpr().start.line
            column = ctx.assignmentExpr().start.column
            self.error_handler.add_error(message, line, column)
            return ErrorType()
            
        return assignment_expr_type


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
                message = f"La condición del operador ? debe ser de tipo 'boolean', no '{logical_or_expr_type}'."
                line = ctx.logicalOrExpr().start.line
                column = ctx.logicalOrExpr().start.column
                self.error_handler.add_error(message, line, column)
            return ErrorType()

        true_out_type = self.visit(ctx.expression(0))
        false_out_type = self.visit(ctx.expression(1))

        if isinstance(true_out_type, ErrorType) or isinstance(false_out_type, ErrorType):
            return ErrorType()
            
        if true_out_type != false_out_type:
            message = f"Las salidas del operador ? deben tener el mismo tipo, pero se encontraron '{true_out_type}' y '{false_out_type}'."
            line = ctx.expression(0).start.line
            column = ctx.expression(0).start.column
            self.error_handler.add_error(message, line, column)
            return ErrorType()

        return true_out_type


    # Visit a parse tree produced by CompiscriptParser#logicalOrExpr.
    def visitLogicalOrExpr(self, ctx:CompiscriptParser.LogicalOrExprContext):
        
        if len(ctx.children) == 1:
            return self.visit(ctx.children[0])

        left_type = self.visit(ctx.children[0])
        right_type = self.visit(ctx.children[2])
        
        op_node = ctx.children[1]
        op_token = op_node.getSymbol()

        if isinstance(left_type, BoolType) and isinstance(right_type, BoolType):
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"El operador lógico '{op_token.text}' solo se puede aplicar a operandos de tipo 'boolean', no a '{left_type}' y '{right_type}'."
        line = op_token.line
        column = op_token.column
        self.error_handler.add_error(message,line,column)
        return ErrorType() 


    # Visit a parse tree produced by CompiscriptParser#logicalAndExpr.
    def visitLogicalAndExpr(self, ctx:CompiscriptParser.LogicalAndExprContext):
        if len(ctx.children) == 1:
            return self.visit(ctx.children[0])

        left_type = self.visit(ctx.children[0])
        right_type = self.visit(ctx.children[2])
        
        op_node = ctx.children[1]
        op_token = op_node.getSymbol()

        if isinstance(left_type, BoolType) and isinstance(right_type, BoolType):
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"El operador lógico '{op_token.text}' solo se puede aplicar a operandos de tipo 'boolean', no a '{left_type}' y '{right_type}'."
        line = op_token.line
        column = op_token.column
        self.error_handler.add_error(message,line,column)
        return ErrorType() 


    # Visit a parse tree produced by CompiscriptParser#equalityExpr.
    def visitEqualityExpr(self, ctx:CompiscriptParser.EqualityExprContext):
        
        if len(ctx.children) == 1:
            return self.visit(ctx.children[0])

        left_type = self.visit(ctx.children[0])
        right_type = self.visit(ctx.children[2])
        
        op_node = ctx.children[1]
        op_token = op_node.getSymbol()

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

        message = f"No se puede realizar la comparación de igualdad '{op_token.text}' entre los tipos '{left_type}' y '{right_type}'."
        line = op_token.line
        column = op_token.column
        self.error_handler.add_error(message, line, column)
        return ErrorType() 


    # Visit a parse tree produced by CompiscriptParser#relationalExpr.
    def visitRelationalExpr(self, ctx:CompiscriptParser.RelationalExprContext):
        
        if len(ctx.children) == 1:
            return self.visit(ctx.children[0])

        left_type = self.visit(ctx.children[0])
        right_type = self.visit(ctx.children[2])
        
        op_node = ctx.children[1]
        op_token = op_node.getSymbol()

        if isinstance(left_type, IntType) and isinstance(right_type, IntType):
            return BoolType()
        
        if isinstance(left_type, ErrorType) or isinstance(right_type, ErrorType):
            return ErrorType()

        message = f"No se puede realizar la comparación '{op_token.text}' entre los tipos '{left_type}' y '{right_type}'."
        line = op_token.line
        column = op_token.column
        self.error_handler.add_error(message, line, column)
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
            else:
            # if current_type is None:
                message = f"El operador '{op_token.text}' no se puede aplicar a operandos de tipos distintos: '{previous_type}' y '{right_type}'."
                line = op_token.line
                column = op_token.column
                self.error_handler.add_error(message, line, column)
                current_type = ErrorType()
                # return None
        
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
                message = f"El operador '{op_token.text}' solo se puede aplicar a operandos de tipo 'integer', no a '{previous_type}' y '{right_type}'."
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
        
        # Propagación de errores
        if isinstance(unary_expr_type, ErrorType):
            return ErrorType()

        op_node = ctx.children[0]
        op_token = op_node.getSymbol()

        if op_token.text == '-':
            if isinstance(unary_expr_type, IntType):
                return IntType()
            else:
                message = f"El operador de negación '-' solo se puede aplicar a operandos de tipo 'integer', no a '{unary_expr_type}'."
                line = op_token.line
                column = op_token.column
                self.error_handler.add_error(message, line, column)
                return ErrorType()

        elif op_token.text == '!':
            if isinstance(unary_expr_type, BoolType):
                return BoolType()
            else:
                message = f"El operador lógico '!' solo se puede aplicar a operandos de tipo 'boolean', no a '{unary_expr_type}'."
                line = op_token.line
                column = op_token.column
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
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:CompiscriptParser.IdentifierExprContext):
        identifier = ctx.getText()
    
        symbol = self.symbol_table.find(identifier)
        
        if not symbol:
            message = f"La variable '{identifier}' no ha sido declarada."
            line = ctx.start.line
            column = ctx.start.column
            self.error_handler.add_error(message, line, column)
            return None

        symbol_type = symbol.data_type
        
        obj_type = self.type_table.find(symbol_type)
        
        if not obj_type:
            message = f"Error interno: El tipo '{symbol_type}' del símbolo '{identifier}' no se encontró en la tabla de tipos."
            line = ctx.start.line
            column = ctx.start.column
            self.error_handler.add_error(message, line, column)
            return None

        return obj_type.data_type


    # Visit a parse tree produced by CompiscriptParser#NewExpr.
    def visitNewExpr(self, ctx:CompiscriptParser.NewExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ThisExpr.
    def visitThisExpr(self, ctx:CompiscriptParser.ThisExprContext):
        return self.visitChildren(ctx)


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
                message = f"No se pueden mezclar tipos en un array. Se esperaba '{first_expression_type}' pero se encontró '{current_expression_type}'."
                self.error_handler.add_error(message, line, column)
                return None 

        return ArrayType(first_expression_type)


    # Visit a parse tree produced by CompiscriptParser#type.
    def visitType(self, ctx:CompiscriptParser.TypeContext):
        
        base_type_name = ctx.baseType().getText()
        base_type_row = self.type_table.find(base_type_name)
        
        if not base_type_row:
            message = f"El tipo base '{base_type_name}' no está definido."
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
