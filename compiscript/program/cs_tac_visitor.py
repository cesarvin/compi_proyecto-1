from visitor.CompiscriptParser import CompiscriptParser
from visitor.CompiscriptVisitor import CompiscriptVisitor
from recursos.custom_types import *
from recursos.error_handler import ErrorHandler
from recursos.symbol_table import *
from recursos.type_table import *
from recursos.tac_handler import *
from cs_type_check_visitor import TypeCheckVisitor

class TACVisitor(CompiscriptVisitor):
    def __init__(self, symbol_table: SymbolTable, type_table: TypeTable):

        super().__init__()
        self.symbol_table = symbol_table
        self.type_table = type_table
        self.loops_count = 0
        self.switchs_count = 0
        self.current_function = None
        self.current_class = None 
        self.current_switch = []
        self.control_switch_cases = []
        
        self.tac = TACode()
        self.label_count = 0

        self.loop_start_labels = [] 
        self.loop_end_labels = [] 
    
    def crear_label(self):
        label = f"_L{self.label_count}"
        self.label_count += 1
        return label
    
    def get_type_addr(self, addr: str, ctx):

        if addr == 'this':
            if self.current_class:
                return self.current_class
        
        elif not addr.startswith('[') and not addr.startswith('t'):
            symbol = self.symbol_table.find(addr)
            if symbol:
                return symbol.data_type
        
        class TempErrorHandler:
            def add_error(self, *args): pass
        
        type_check = TypeCheckVisitor(TempErrorHandler(), self.symbol_table, self.type_table)
        type_check.current_class = self.current_class 
        return type_check.visit(ctx)


    # Visit a parse tree produced by CompiscriptParser#program.
    def visitProgram(self, ctx:CompiscriptParser.ProgramContext):
        self.visitChildren(ctx)
        return self.tac


    # Visit a parse tree produced by CompiscriptParser#statement.
    def visitStatement(self, ctx:CompiscriptParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#block.
    def visitBlock(self, ctx:CompiscriptParser.BlockContext):
        self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:CompiscriptParser.VariableDeclarationContext):
        
        variable = ctx.Identifier().getText()
        
        symbol = self.symbol_table.find_in_current_scope(variable)
        if not symbol:
            symbol_to_clone = self.symbol_table.find(variable)
            if symbol_to_clone:
                self.symbol_table.add(symbol_to_clone)
                symbol = symbol_to_clone

        if ctx.initializer():
            right_side_addr = self.visit(ctx.initializer().expression())
            
            symbol = self.symbol_table.find(variable)
            if symbol and symbol.offset is not None:
                left_side_addr = f"[BP+{symbol.offset}]"
                self.tac.add_quadruple('=', right_side_addr, None, left_side_addr)
            else:
                print(f"ADVERTENCIA: No se encontró el símbolo '{variable}' durante la generación de TAC.")

        return None


    # Visit a parse tree produced by CompiscriptParser#constantDeclaration.
    def visitConstantDeclaration(self, ctx:CompiscriptParser.ConstantDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#typeAnnotation.
    def visitTypeAnnotation(self, ctx:CompiscriptParser.TypeAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#initializer.
    def visitInitializer(self, ctx:CompiscriptParser.InitializerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#assignment.
    def visitAssignment(self, ctx:CompiscriptParser.AssignmentContext):

        is_prop_assign = ctx.getChild(1).getText() == '.'
        
        ctx_expresion = ctx.expression(1) if is_prop_assign else ctx.expression(0)
        right_addr = self.visit(ctx_expresion)
        left_addr = None

        if is_prop_assign:
            obj_var_addr = self.visit(ctx.expression(0))
            obj_base_addr = self.tac.add_temp()

            self.tac.add_quadruple('=', obj_var_addr, None, obj_base_addr)

            type_addr = self.get_type_addr(obj_var_addr, ctx.expression(0))
            ctx_identifier = ctx.Identifier().getText()

            if isinstance(type_addr, ClassType):
                clase = str(type_addr)
                class_type = self.type_table.find(clase)
            
                if class_type and ctx_identifier in class_type.attributes:
                    prop_info = class_type.attributes[ctx_identifier]
                    prop_offset = prop_info['offset'] 
                    left_addr = f"[{obj_base_addr}+{prop_offset}]" 
        else:

            variable = ctx.Identifier().getText()
            symbol = self.symbol_table.find(variable)
            if symbol and symbol.offset is not None:
                left_addr = f"[BP+{symbol.offset}]"

        if left_addr and right_addr:
            self.tac.add_quadruple('=', right_addr, None, left_addr)

        return None


    # Visit a parse tree produced by CompiscriptParser#expressionStatement.
    def visitExpressionStatement(self, ctx:CompiscriptParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#printStatement.
    def visitPrintStatement(self, ctx:CompiscriptParser.PrintStatementContext):
        ctx_expression = self.visit(ctx.expression())
        self.tac.add_quadruple('PARAM', arg1=ctx_expression)
        self.tac.add_quadruple('CALL', arg1='print', arg2='1')
        return None


    # Visit a parse tree produced by CompiscriptParser#ifStatement.
    def visitIfStatement(self, ctx:CompiscriptParser.IfStatementContext):
        ctx_expresion = self.visit(ctx.expression())
        def_else = len(ctx.block()) > 1
        else_label = self.crear_label()
        end_label = self.crear_label()
        target_label = else_label if def_else else end_label
        self.tac.add_quadruple(op='IF_FALSE', arg1=ctx_expresion, result=target_label)
        self.visit(ctx.block(0))

        if def_else:
            self.tac.add_quadruple(op='GOTO', result=end_label)
            self.tac.add_quadruple(op=else_label + ':')
            self.visit(ctx.block(1))

        self.tac.add_quadruple(op=end_label + ':')

        return None


    # Visit a parse tree produced by CompiscriptParser#whileStatement.
    def visitWhileStatement(self, ctx:CompiscriptParser.WhileStatementContext):

        start_label = self.crear_label()
        end_label = self.crear_label()

        self.loop_start_labels.append(start_label)
        self.loop_end_labels.append(end_label)
        self.tac.add_quadruple(op=start_label + ':')

        ctx_expresion = self.visit(ctx.expression())
        
        self.tac.add_quadruple(op='IF_FALSE', arg1=ctx_expresion, result=end_label)
        self.visit(ctx.block())
        self.tac.add_quadruple(op='GOTO', result=start_label)
        self.tac.add_quadruple(op=end_label + ':')
        self.loop_start_labels.pop()
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:CompiscriptParser.DoWhileStatementContext):
        start_label = self.crear_label()
        end_label = self.crear_label()
        condition_label = self.crear_label()
        
        self.loop_start_labels.append(condition_label)
        self.loop_end_labels.append(end_label)         
        self.tac.add_quadruple(op=start_label + ':')
        self.visit(ctx.block())
        self.tac.add_quadruple(op=condition_label + ':')
        
        ctx_expresion = self.visit(ctx.expression())
        
        self.tac.add_quadruple(op='IF_TRUE', arg1=ctx_expresion, result=start_label)
        self.tac.add_quadruple(op=end_label + ':')
        self.loop_start_labels.pop()
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#forStatement.
    def visitForStatement(self, ctx:CompiscriptParser.ForStatementContext):
        
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())

        start_label = self.crear_label()
        continue_label = self.crear_label()
        end_label = self.crear_label()
        
        self.loop_start_labels.append(continue_label)
        self.loop_end_labels.append(end_label)
        self.tac.add_quadruple(op=start_label + ':')
        
        if ctx.expression(0):
            ctx_expresion = self.visit(ctx.expression(0))
            self.tac.add_quadruple(op='IF_FALSE', arg1=ctx_expresion, result=end_label)
        
        self.visit(ctx.block())
        self.tac.add_quadruple(op=continue_label + ':')
        
        if ctx.expression(1):
            self.visit(ctx.expression(1))
            
        self.tac.add_quadruple(op='GOTO', result=start_label)
        self.tac.add_quadruple(op=end_label + ':')
        self.loop_start_labels.pop()
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#foreachStatement.
    def visitForeachStatement(self, ctx:CompiscriptParser.ForeachStatementContext):

        ctx_expresion = self.visit(ctx.expression())
        expresion_type = self.get_type_addr(ctx_expresion, ctx.expression())

        num_elements = 3 
        element_size = 8 
        
        index_temp = self.tac.add_temp()
        self.tac.add_quadruple('=', '0', None, index_temp) 

        start_label = self.crear_label()
        end_label = self.crear_label()

        self.tac.add_quadruple(op=start_label + ':')

        cond_temp = self.tac.add_temp()
        self.tac.add_quadruple('<', index_temp, str(num_elements), cond_temp)
        self.tac.add_quadruple('IF_FALSE', cond_temp, None, end_label)

        self.symbol_table.enter_scope()

        offset_temp = self.tac.add_temp()
        self.tac.add_quadruple('*', index_temp, str(element_size), offset_temp)
        addr_temp = self.tac.add_temp()
        self.tac.add_quadruple('+', ctx_expresion, offset_temp, addr_temp)

        current_element_val = self.tac.add_temp()
        self.tac.add_quadruple('=', f"[{addr_temp}]", None, current_element_val)

        loop_var_name = ctx.Identifier().getText()
        loop_var_symbol = VariableSymbol(id=loop_var_name, data_type=expresion_type.element_type, size=element_size)
        self.symbol_table.add(loop_var_symbol) 

        loop_var_addr = f"[BP+{loop_var_symbol.offset}]"
        self.tac.add_quadruple('=', current_element_val, None, loop_var_addr)

        self.visit(ctx.block())

        inc_temp = self.tac.add_temp()
        self.tac.add_quadruple('+', index_temp, '1', inc_temp)
        self.tac.add_quadruple('=', inc_temp, None, index_temp) 

        self.tac.add_quadruple('GOTO', None, None, start_label)

        self.tac.add_quadruple(op=end_label + ':')
        self.symbol_table.exit_scope()

        return None


    # Visit a parse tree produced by CompiscriptParser#breakStatement.
    def visitBreakStatement(self, ctx:CompiscriptParser.BreakStatementContext):
        if self.loop_end_labels:
            end_label = self.loop_end_labels[-1]
            self.tac.add_quadruple(op='GOTO', result=end_label)
        
        return None


    # Visit a parse tree produced by CompiscriptParser#continueStatement.
    def visitContinueStatement(self, ctx:CompiscriptParser.ContinueStatementContext):
        if self.loop_start_labels:
            start_label = self.loop_start_labels[-1]
            self.tac.add_quadruple(op='GOTO', result=start_label)
        return None


    # Visit a parse tree produced by CompiscriptParser#returnStatement.
    def visitReturnStatement(self, ctx:CompiscriptParser.ReturnStatementContext):
        if ctx.expression():
            return_addr = self.visit(ctx.expression())
            self.tac.add_quadruple(op='RETURN', arg1=return_addr)
        else:
            
            self.tac.add_quadruple(op='RETURN')
        return None


    # Visit a parse tree produced by CompiscriptParser#tryCatchStatement.
    def visitTryCatchStatement(self, ctx:CompiscriptParser.TryCatchStatementContext):

        catch_label = self.crear_label()
        end_label = self.crear_label()

        self.tac.add_quadruple(op='TRY_BEGIN', arg1=catch_label)
        self.visit(ctx.block(0))
        self.tac.add_quadruple(op='TRY_END')
        self.tac.add_quadruple(op='GOTO', result=end_label)
        self.tac.add_quadruple(op=catch_label + ':')
        self.symbol_table.enter_scope()
        
        exception_var_name = ctx.Identifier().getText()
        symbol = self.symbol_table.find(exception_var_name)

        if symbol:
            pass

        self.visit(ctx.block(1))
        self.symbol_table.exit_scope()
        self.tac.add_quadruple(op=end_label + ':')

        return None


    # Visit a parse tree produced by CompiscriptParser#switchStatement.
    def visitSwitchStatement(self, ctx:CompiscriptParser.SwitchStatementContext):

        switch_addr = self.visit(ctx.expression())
        case_labels = [self.crear_label() for _ in ctx.switchCase()]
        default_label = self.crear_label() if ctx.defaultCase() else None
        end_label = self.crear_label()

        self.loop_end_labels.append(end_label) 

        for i, case_ctx in enumerate(ctx.switchCase()):
            case_addr = self.visit(case_ctx.expression())
            cond_temp = self.tac.add_temp()
            self.tac.add_quadruple('==', switch_addr, case_addr, cond_temp)
            self.tac.add_quadruple('IF_TRUE', cond_temp, None, case_labels[i])

        if default_label:
            self.tac.add_quadruple('GOTO', None, None, default_label)
        else: 
            self.tac.add_quadruple('GOTO', None, None, end_label)

        for i, case_ctx in enumerate(ctx.switchCase()):
            self.tac.add_quadruple(op=case_labels[i] + ':')

            for stmt in case_ctx.statement():
                self.visit(stmt)

        if default_label:
            self.tac.add_quadruple(op=default_label + ':')

            for stmt in ctx.defaultCase().statement():
                self.visit(stmt)

        self.tac.add_quadruple(op=end_label + ':')
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#switchCase.
    def visitSwitchCase(self, ctx:CompiscriptParser.SwitchCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#defaultCase.
    def visitDefaultCase(self, ctx:CompiscriptParser.DefaultCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#functionDeclaration.
    def visitFunctionDeclaration(self, ctx:CompiscriptParser.FunctionDeclarationContext):
        funcion = ctx.Identifier().getText()

        self.tac.add_quadruple(op=f'{funcion}:')
        self.tac.add_quadruple(op='BEGIN_FUNC')

        self.symbol_table.enter_scope()

        if self.current_class:
            this_symbol = VariableSymbol(id='this', data_type=self.current_class, size=8, role='Parameter', offset=0)
            self.symbol_table.add(this_symbol)
            
            full_method_name = f"{self.current_class}.{funcion}" if funcion != "constructor" else funcion
            method_symbol = self.symbol_table.scopes[-2]['symbols'].get(full_method_name) 

            if method_symbol and isinstance(method_symbol.data_type, FunctionType):
                param_offset_start = 8 
                
                param_nodes = []
                if ctx.parameters():
                    param_nodes = ctx.parameters().parameter()

                for i, param_node in enumerate(param_nodes):
                    param_name = param_node.Identifier().getText()
                    param_type = method_symbol.data_type.param_types[i]
                    type_row = self.type_table.find(str(param_type))
                    
                    param_symbol = VariableSymbol(
                        id=param_name, data_type=param_type,
                        size=type_row.size if type_row else 8, role='Parameter',
                        offset=param_offset_start + (i * 8)
                    )
                    self.symbol_table.add(param_symbol)
        else:
            func_symbol = self.symbol_table.scopes[0]['symbols'].get(funcion)
            
            if func_symbol and isinstance(func_symbol.data_type, FunctionType):
                param_offset_start = 8 
                
                param_nodes = []
                if ctx.parameters():
                    param_nodes = ctx.parameters().parameter()

                for i, param_node in enumerate(param_nodes):
                    param_name = param_node.Identifier().getText()
                    param_type = func_symbol.data_type.param_types[i]
                    type_row = self.type_table.find(str(param_type))
                    
                    param_symbol = VariableSymbol(
                        id=param_name,
                        data_type=param_type,
                        size=type_row.size if type_row else 8,
                        role='Parameter',
                        offset=param_offset_start + (i * 8)
                    )
                    self.symbol_table.add(param_symbol)
        
        self.visit(ctx.block())
        self.symbol_table.exit_scope()

        self.tac.add_quadruple(op='END_FUNC')
        return None

        # funcion = ctx.Identifier().getText()

        # self.tac.add_quadruple(op=f'{funcion}:')
        # self.tac.add_quadruple(op='BEGIN_FUNC')
        # self.symbol_table.enter_scope()
        
        # if self.current_class:
        #     this_symbol = VariableSymbol(id='this', data_type=self.current_class, size=8, role='Parameter', offset=0)
        #     self.symbol_table.add(this_symbol)
            
        #     metodo = f"{self.current_class}.{funcion}" if funcion != "constructor" else funcion
        #     metodo_symbol = self.symbol_table.find(metodo)

        #     if metodo_symbol and isinstance(metodo_symbol.data_type, FunctionType):
        #         param_offset_start = 8 

        #         for i, param in enumerate(metodo_symbol.parameters):
        #             param.offset = param_offset_start + (i * 8) 
        #             self.symbol_table.add(param)

        # self.visit(ctx.block())
        # self.symbol_table.exit_scope()

        # self.tac.add_quadruple(op='END_FUNC')
        
        # return None


    # Visit a parse tree produced by CompiscriptParser#parameters.
    def visitParameters(self, ctx:CompiscriptParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameter.
    def visitParameter(self, ctx:CompiscriptParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classDeclaration.
    def visitClassDeclaration(self, ctx:CompiscriptParser.ClassDeclarationContext):
        clase = ctx.Identifier(0).getText()
        clase_tipo = self.type_table.find(clase)

        if not clase_tipo: 
            return
        
        previous_class = self.current_class
        self.current_class = clase_tipo.data_type

        self.symbol_table.enter_scope()

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

        ctx_assignacion = self.visit(ctx.assignmentExpr())
        left_side_addr = self.visitLeftHandSide(ctx.lhs, load_value=False)

        self.tac.add_quadruple('=', ctx_assignacion, None, left_side_addr)

        return ctx_assignacion


    # Visit a parse tree produced by CompiscriptParser#PropertyAssignExpr.
    def visitPropertyAssignExpr(self, ctx:CompiscriptParser.PropertyAssignExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ExprNoAssign.
    def visitExprNoAssign(self, ctx:CompiscriptParser.ExprNoAssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#TernaryExpr.
    def visitTernaryExpr(self, ctx:CompiscriptParser.TernaryExprContext):

        if len(ctx.expression()) == 0:
            return self.visit(ctx.logicalOrExpr())

        result_addr = self.tac.add_temp()

        false_label = self.crear_label()
        end_label = self.crear_label()
        ctx_logical_or = self.visit(ctx.logicalOrExpr())
        self.tac.add_quadruple('IF_FALSE', ctx_logical_or, None, false_label)
        ctx_expresion = self.visit(ctx.expression(0))
        self.tac.add_quadruple('=', ctx_expresion, None, result_addr)
        self.tac.add_quadruple('GOTO', None, None, end_label)
        self.tac.add_quadruple(op=false_label + ':')
        false_addr = self.visit(ctx.expression(1))
        self.tac.add_quadruple('=', false_addr, None, result_addr)
        self.tac.add_quadruple(op=end_label + ':')

        return result_addr


    # Visit a parse tree produced by CompiscriptParser#logicalOrExpr.
    def visitLogicalOrExpr(self, ctx:CompiscriptParser.LogicalOrExprContext):
        operadores = ctx.logicalAndExpr() 

        if len(operadores) == 1:
            return self.visit(operadores[0])

        left_addr = self.visit(operadores[0])
        right_addr = self.visit(operadores[1])
        result_addr = self.tac.add_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_quadruple(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#logicalAndExpr.
    def visitLogicalAndExpr(self, ctx:CompiscriptParser.LogicalAndExprContext):
        operadores = ctx.equalityExpr() 

        if len(operadores) == 1:
            return self.visit(operadores[0])

        left_addr = self.visit(operadores[0])
        right_addr = self.visit(operadores[1])
        result_addr = self.tac.add_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_quadruple(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#equalityExpr.
    def visitEqualityExpr(self, ctx:CompiscriptParser.EqualityExprContext):
        operadores = ctx.relationalExpr() 
        if len(operadores) == 1:
            return self.visit(operadores[0])

        left_addr = self.visit(operadores[0])
        right_addr = self.visit(operadores[1])
        result_addr = self.tac.add_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_quadruple(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#relationalExpr.
    def visitRelationalExpr(self, ctx:CompiscriptParser.RelationalExprContext):

        if len(ctx.additiveExpr()) == 1:
            return self.visit(ctx.additiveExpr(0))

        left_addr = self.visit(ctx.additiveExpr(0))
        right_addr = self.visit(ctx.additiveExpr(1))
        result_addr = self.tac.add_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_quadruple(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#additiveExpr.
    def visitAdditiveExpr(self, ctx:CompiscriptParser.AdditiveExprContext):
        
        if len(ctx.multiplicativeExpr()) == 1:
            return self.visit(ctx.multiplicativeExpr(0))

        
        left_addr = self.visit(ctx.multiplicativeExpr(0))
        right_addr = self.visit(ctx.multiplicativeExpr(1))
        result_addr = self.tac.add_temp() 
        op = ctx.getChild(1).getText()
        
        self.tac.add_quadruple(op, left_addr, right_addr, result_addr)

        return result_addr


    # Visit a parse tree produced by CompiscriptParser#multiplicativeExpr.
    def visitMultiplicativeExpr(self, ctx:CompiscriptParser.MultiplicativeExprContext):
        
        if len(ctx.unaryExpr()) == 1:
            return self.visit(ctx.unaryExpr(0))
        
        left_addr = self.visit(ctx.unaryExpr(0))
        right_addr = self.visit(ctx.unaryExpr(1))
        result_addr = self.tac.add_temp()
        op = ctx.getChild(1).getText()
        self.tac.add_quadruple(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#unaryExpr.
    def visitUnaryExpr(self, ctx:CompiscriptParser.UnaryExprContext):
        
        if ctx.primaryExpr():
            return self.visit(ctx.primaryExpr())
        
        operand_addr = self.visit(ctx.unaryExpr())
        op = ctx.getChild(0).getText()
        result_addr = self.tac.add_temp()
        
        if op == '-':
            self.tac.add_quadruple(op, '0', operand_addr, result_addr)
        elif op == '!':
            self.tac.add_quadruple('==', operand_addr, 'false', result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#primaryExpr.
    def visitPrimaryExpr(self, ctx:CompiscriptParser.PrimaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#literalExpr.
    def visitLiteralExpr(self, ctx:CompiscriptParser.LiteralExprContext):

        if ctx.literal():
            return self.visit(ctx.literal())
        elif ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        else:
            return ctx.getText()


    # Visit a parse tree produced by CompiscriptParser#literal.
    def visitLiteral(self, ctx:CompiscriptParser.LiteralContext):
        return ctx.getText()


    # Visit a parse tree produced by CompiscriptParser#leftHandSide.
    def visitLeftHandSide(self, ctx:CompiscriptParser.LeftHandSideContext, load_value=True):
        
        current_addr = self.visit(ctx.primaryAtom())
        current_type = self.get_type_addr(current_addr, ctx.primaryAtom())

        for suffix in ctx.suffixOp():
            
            if isinstance(current_type, ErrorType): 
                return ErrorType()

            if isinstance(suffix, CompiscriptParser.CallExprContext):
                arg_addrs = []
                
                if suffix.arguments():
                    for arg_expr in suffix.arguments().expression():
                        arg_addr = self.visit(arg_expr)
                        self.tac.add_quadruple(op='PARAM', arg1=arg_addr)
                        arg_addrs.append(arg_addr)
                
                result_addr = self.tac.add_temp()
                num_args = len(arg_addrs)
                self.tac.add_quadruple(op='CALL', arg1=current_addr, arg2=str(num_args), result=result_addr)
                
                current_addr = result_addr

                if isinstance(current_type, FunctionType):
                    current_type = current_type.return_type

            elif isinstance(suffix, CompiscriptParser.PropertyAccessExprContext):
                prop_name = suffix.Identifier().getText()
                
                if isinstance(current_type, ClassType):
                    class_name = str(current_type)
                    class_type_row = self.type_table.find(class_name)
                    
                    if class_type_row and prop_name in class_type_row.attributes:
                        prop_info = class_type_row.attributes[prop_name]
                        
                        if isinstance(prop_info, FunctionType):
                            current_addr = f"{class_name}.{prop_name}"
                            current_type = prop_info
                        else:
                            prop_type = prop_info['type']
                            prop_offset = prop_info['offset']
                            prop_addr = f"[{current_addr}+{prop_offset}]"
                            
                            if load_value:
                                value_temp = self.tac.add_temp()
                                self.tac.add_quadruple('=', prop_addr, None, value_temp)
                                current_addr = value_temp
                            else:
                                current_addr = prop_addr
                            
                            current_type = prop_type

            elif isinstance(suffix, CompiscriptParser.IndexExprContext):
                if isinstance(current_type, ArrayType):
                    index_addr = self.visit(suffix.expression())
                    element_type = current_type.element_type

                    type_row = self.type_table.find(str(element_type))
                    element_size = str(type_row.size) if type_row else "8"

                    
                    offset_temp = self.tac.add_temp()
                    self.tac.add_quadruple('*', index_addr, element_size, offset_temp)
        
                    final_addr_temp = self.tac.add_temp()
                    self.tac.add_quadruple('+', current_addr, offset_temp, final_addr_temp)
        
                    if load_value:
                        value_temp = self.tac.add_temp()
                        self.tac.add_quadruple('=', f"[{final_addr_temp}]", None, value_temp)
                        current_addr = value_temp
                    else:
                        current_addr = f"[{final_addr_temp}]"
                    
                    current_type = element_type

        return current_addr


    # Visit a parse tree produced by CompiscriptParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:CompiscriptParser.IdentifierExprContext):
        variable = ctx.getText()
        symbol = self.symbol_table.find(variable)
        
        if symbol and hasattr(symbol, 'offset') and symbol.offset is not None:
            return f"[BP+{symbol.offset}]"
        
        return variable


    # Visit a parse tree produced by CompiscriptParser#NewExpr.
    def visitNewExpr(self, ctx:CompiscriptParser.NewExprContext):
        clase = ctx.Identifier().getText()
        args_count = 0
        
        if ctx.arguments():
            args_count = len(ctx.arguments().expression())
            for arg_expr in ctx.arguments().expression():
                arg_addr = self.visit(arg_expr)
                self.tac.add_quadruple(op='PARAM', arg1=arg_addr)
        
        result_addr = self.tac.add_temp()

        self.tac.add_quadruple(op='NEW', arg1=clase, arg2=str(args_count), result=result_addr)

        return result_addr


    # Visit a parse tree produced by CompiscriptParser#ThisExpr.
    def visitThisExpr(self, ctx:CompiscriptParser.ThisExprContext):
        return 'this'


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

        element_addrs = [self.visit(expr) for expr in ctx.expression()]
        num_elements = len(element_addrs)
        element_size = 8 
        total_size = num_elements * element_size

        base_addr = self.tac.add_temp()

        self.tac.add_quadruple(op='ALLOCATE', arg1=str(total_size), result=base_addr)

        current_offset = 0
        for addr in element_addrs:

            dest_addr = f"[{base_addr}+{current_offset}]"
            self.tac.add_quadruple('=', addr, None, dest_addr)
            current_offset += element_size

        return base_addr


    # Visit a parse tree produced by CompiscriptParser#type.
    def visitType(self, ctx:CompiscriptParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#baseType.
    def visitBaseType(self, ctx:CompiscriptParser.BaseTypeContext):
        return self.visitChildren(ctx)

