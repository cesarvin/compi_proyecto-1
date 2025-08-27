from visitor.CompiscriptParser import CompiscriptParser
from visitor.CompiscriptVisitor import CompiscriptVisitor
from recursos.custom_types import IntType, StringType, BoolType, ObjectType, ArrayType
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
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:CompiscriptParser.VariableDeclarationContext):
        
        ctx_identifier = ctx.Identifier().getText()
        
        
        if self.symbol_table.find_in_current_scope(ctx_identifier):
            self.error_handler.add_error(
                f"La variable '{ctx_identifier}' ya ha sido declarada en este ámbito.",
                ctx.start.line,
                ctx.start.column
            )
            return

        annotated_type_obj = None
        inferred_type_obj = None

        if ctx.typeAnnotation():
            type_name = ctx.typeAnnotation().type_().getText()
            annotated_type_obj = self.type_table.find(type_name)
            if not annotated_type_obj:
                self.error_handler.add_error(
                    f"El tipo '{type_name}' no está definido.",
                    ctx.typeAnnotation().start.line,
                    ctx.typeAnnotation().start.column
                )
                return

        if ctx.initializer():
            inferred_type_obj = self.visit(ctx.initializer().expression())
            if not inferred_type_obj:
                return

        final_type_row = None
        if annotated_type_obj and inferred_type_obj:
            if annotated_type_obj.data_type != inferred_type_obj:
                self.error_handler.add_error(
                    f"No se puede asignar un valor de tipo '{inferred_type_obj}' a una variable de tipo '{annotated_type_obj.data_type}'.",
                    ctx.initializer().start.line,
                    ctx.initializer().start.column
                )
                return
            final_type_row = annotated_type_obj
        elif annotated_type_obj:
            final_type_row = annotated_type_obj
        elif inferred_type_obj:
            final_type_row = self.type_table.find(str(inferred_type_obj))
        else:
            self.error_handler.add_error(
                f"La variable '{ctx_identifier}' debe tener un tipo o un valor inicial.",
                ctx.start.line,
                ctx.start.column
            )
            return

        if final_type_row:
            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0

            new_symbol = SymbolRow(
                id=ctx_identifier,
                data_type=str(final_type_row.data_type), 
                size=final_type_row.size,
                scope=scope_level,
                parent_scope=parent_level,
                is_param='Variable'
            )
            self.symbol_table.add(new_symbol)


    # Visit a parse tree produced by CompiscriptParser#constantDeclaration.
    def visitConstantDeclaration(self, ctx:CompiscriptParser.ConstantDeclarationContext):
        ctx_identifier = ctx.Identifier().getText()

        if self.symbol_table.find_in_current_scope(ctx_identifier):
            self.error_handler.add_error(
                f"El identificador '{ctx_identifier}' ya ha sido declarado en este ámbito.",
                ctx.start.line,
                ctx.start.column
            )
            return

        annotated_type_obj = None
        
        if ctx.typeAnnotation():
            type_name = ctx.typeAnnotation().type_().getText()
            annotated_type_obj = self.type_table.find(type_name)
            if not annotated_type_obj:
                self.error_handler.add_error(
                    f"El tipo '{type_name}' no está definido.",
                    ctx.typeAnnotation().start.line,
                    ctx.typeAnnotation().start.column
                )
                return

        inferred_type_obj = self.visit(ctx.expression())
        if not inferred_type_obj:
            return # Error al evaluar la expresión

        final_type_row = None
        if annotated_type_obj:
            if str(annotated_type_obj.data_type) != str(inferred_type_obj):
                self.error_handler.add_error(
                    f"No se puede asignar un valor de tipo '{inferred_type_obj}' a una constante de tipo '{annotated_type_obj.data_type}'.",
                    ctx.expression().start.line,
                    ctx.expression().start.column
                )
                return
            final_type_row = annotated_type_obj
        else:
            final_type_row = self.type_table.find(str(inferred_type_obj))

        if final_type_row:
            scope_level = self.symbol_table.get_current_scope_level()
            parent_level = scope_level - 1 if scope_level > 1 else 0

            new_symbol = SymbolRow(
                id=ctx_identifier,
                data_type=str(final_type_row.data_type),
                size=final_type_row.size,
                scope=scope_level,
                parent_scope=parent_level,
                is_param='Constant'  # <-- ✨ Diferencia Clave
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
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#expressionStatement.
    def visitExpressionStatement(self, ctx:CompiscriptParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#printStatement.
    def visitPrintStatement(self, ctx:CompiscriptParser.PrintStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ifStatement.
    def visitIfStatement(self, ctx:CompiscriptParser.IfStatementContext):
        return self.visitChildren(ctx)


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
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#PropertyAssignExpr.
    def visitPropertyAssignExpr(self, ctx:CompiscriptParser.PropertyAssignExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ExprNoAssign.
    def visitExprNoAssign(self, ctx:CompiscriptParser.ExprNoAssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#TernaryExpr.
    def visitTernaryExpr(self, ctx:CompiscriptParser.TernaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#logicalOrExpr.
    def visitLogicalOrExpr(self, ctx:CompiscriptParser.LogicalOrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#logicalAndExpr.
    def visitLogicalAndExpr(self, ctx:CompiscriptParser.LogicalAndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#equalityExpr.
    def visitEqualityExpr(self, ctx:CompiscriptParser.EqualityExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#relationalExpr.
    def visitRelationalExpr(self, ctx:CompiscriptParser.RelationalExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#additiveExpr.
    def visitAdditiveExpr(self, ctx:CompiscriptParser.AdditiveExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#multiplicativeExpr.
    def visitMultiplicativeExpr(self, ctx:CompiscriptParser.MultiplicativeExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#unaryExpr.
    def visitUnaryExpr(self, ctx:CompiscriptParser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#primaryExpr.
    def visitPrimaryExpr(self, ctx:CompiscriptParser.PrimaryExprContext):
        type = self.visitChildren(ctx)
        return type


    # Visit a parse tree produced by CompiscriptParser#literalExpr.
    def visitLiteralExpr(self, ctx:CompiscriptParser.LiteralExprContext):

        ctx_text = ctx.getText()
        
        if ctx_text=="true" or ctx_text=="false":
            return BoolType()
        
        elif ctx_text=="null":
            return ObjectType()
       
        elif ctx.literal():
            literal_ctx = ctx.literal()
            
            if literal_ctx.IntegerLiteral():
                return IntType()
            elif literal_ctx.StringLiteral():
                return StringType()

        elif ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        
        return None


    # Visit a parse tree produced by CompiscriptParser#leftHandSide.
    def visitLeftHandSide(self, ctx:CompiscriptParser.LeftHandSideContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:CompiscriptParser.IdentifierExprContext):
        return self.visitChildren(ctx)


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
        expressions = ctx.expression()

        if not expressions:
            return ArrayType(ObjectType())

        # si hay elementos, obtenemos el tipo del primer elemento
        first_element_type = self.visit(expressions[0])
        
        for i in range(1, len(expressions)):
            current_element_type = self.visit(expressions[i])
            
            # se comparan todos los tipos con el del primer elemento
            if current_element_type != first_element_type:
                line = expressions[i].start.line
                column = expressions[i].start.column
                message = (f"No se pueden mezclar tipos en un array. "
                           f"Se esperaba '{first_element_type}' pero se encontró '{current_element_type}'.")
                self.error_handler.add_error(message, line, column)
                return None 

        return ArrayType(first_element_type)


    # Visit a parse tree produced by CompiscriptParser#type.
    def visitType(self, ctx:CompiscriptParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#baseType.
    def visitBaseType(self, ctx:CompiscriptParser.BaseTypeContext):
        return self.visitChildren(ctx)
