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
        self.label_counter = 0

        self.loop_start_labels = [] 
        self.loop_end_labels = [] 
    
    def new_label(self):
        label_name = f"_L{self.label_counter}"
        self.label_counter += 1
        return label_name
    
    def _get_type_from_addr(self, addr: str, ctx):
        
        if addr == 'this':
            if self.current_class:
                return self.current_class
        
        elif not addr.startswith('[') and not addr.startswith('t'):
            symbol = self.symbol_table.find(addr)
            if symbol:
                return symbol.data_type
        
        class DummyErrorHandler:
            def add_error(self, *args): pass
        
        type_checker = TypeCheckVisitor(DummyErrorHandler(), self.symbol_table, self.type_table)
        type_checker.current_class = self.current_class # Sincronizamos el estado
        return type_checker.visit(ctx)


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
                self.tac.add_instruction('=', right_side_addr, None, left_side_addr)
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
        expr_node = ctx.expression(1) if is_prop_assign else ctx.expression(0)
        right_side_addr = self.visit(expr_node)

        left_side_addr = None
        
        if is_prop_assign:
            
            base_addr = self.visit(ctx.expression(0))  # Dirección de 'this'
            base_type = self._get_type_from_addr(base_addr, ctx.expression(0))
            prop_name = ctx.Identifier().getText()     # Nombre de la propiedad 'name'

            if isinstance(base_type, ClassType):
                class_name = str(base_type)
                class_type_row = self.type_table.find(class_name)
                if class_type_row and prop_name in class_type_row.attributes:
                    prop_offset = 0 
                    left_side_addr = f"[{base_addr}+{prop_offset}]" # ej. [this+0]
        else:
            var_name = ctx.Identifier().getText()
            symbol = self.symbol_table.find(var_name)
            if symbol and symbol.offset is not None:
                left_side_addr = f"[BP+{symbol.offset}]"
        
        
        if left_side_addr and right_side_addr:
            self.tac.add_instruction('=', right_side_addr, None, left_side_addr)
        
        return None


    # Visit a parse tree produced by CompiscriptParser#expressionStatement.
    def visitExpressionStatement(self, ctx:CompiscriptParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#printStatement.
    def visitPrintStatement(self, ctx:CompiscriptParser.PrintStatementContext):
        expr_addr = self.visit(ctx.expression())
        self.tac.add_instruction('PARAM', arg1=expr_addr)
        self.tac.add_instruction('CALL', arg1='print', arg2='1')
        return None


    # Visit a parse tree produced by CompiscriptParser#ifStatement.
    def visitIfStatement(self, ctx:CompiscriptParser.IfStatementContext):
        condition_addr = self.visit(ctx.expression())
        has_else = len(ctx.block()) > 1
        else_label = self.new_label()
        end_label = self.new_label()
        target_label = else_label if has_else else end_label
        self.tac.add_instruction(op='IF_FALSE', arg1=condition_addr, result=target_label)
        self.visit(ctx.block(0))

        if has_else:
            self.tac.add_instruction(op='GOTO', result=end_label)
            self.tac.add_instruction(op=else_label + ':')
            self.visit(ctx.block(1))

        self.tac.add_instruction(op=end_label + ':')

        return None


    # Visit a parse tree produced by CompiscriptParser#whileStatement.
    def visitWhileStatement(self, ctx:CompiscriptParser.WhileStatementContext):

        start_label = self.new_label()
        end_label = self.new_label()

        self.loop_start_labels.append(start_label)
        self.loop_end_labels.append(end_label)
        self.tac.add_instruction(op=start_label + ':')

        condition_addr = self.visit(ctx.expression())

        self.tac.add_instruction(op='IF_FALSE', arg1=condition_addr, result=end_label)
        self.visit(ctx.block())
        self.tac.add_instruction(op='GOTO', result=start_label)
        self.tac.add_instruction(op=end_label + ':')
        self.loop_start_labels.pop()
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:CompiscriptParser.DoWhileStatementContext):
        start_label = self.new_label()
        end_label = self.new_label()
        condition_label = self.new_label()
        self.loop_start_labels.append(condition_label) # 'continue' salta a la condición
        self.loop_end_labels.append(end_label)         
        self.tac.add_instruction(op=start_label + ':')
        self.visit(ctx.block())
        self.tac.add_instruction(op=condition_label + ':')
        condition_addr = self.visit(ctx.expression())
        self.tac.add_instruction(op='IF_TRUE', arg1=condition_addr, result=start_label)
        self.tac.add_instruction(op=end_label + ':')
        self.loop_start_labels.pop()
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#forStatement.
    def visitForStatement(self, ctx:CompiscriptParser.ForStatementContext):
        
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())

        start_label = self.new_label()
        continue_label = self.new_label()
        end_label = self.new_label()
        
        self.loop_start_labels.append(continue_label)
        self.loop_end_labels.append(end_label)
        self.tac.add_instruction(op=start_label + ':')
        
        if ctx.expression(0):
            condition_addr = self.visit(ctx.expression(0))
            self.tac.add_instruction(op='IF_FALSE', arg1=condition_addr, result=end_label)
        
        self.visit(ctx.block())
        self.tac.add_instruction(op=continue_label + ':')
        
        if ctx.expression(1):
            self.visit(ctx.expression(1))
            
        self.tac.add_instruction(op='GOTO', result=start_label)
        self.tac.add_instruction(op=end_label + ':')
        self.loop_start_labels.pop()
        self.loop_end_labels.pop()

        return None


    # Visit a parse tree produced by CompiscriptParser#foreachStatement.
    def visitForeachStatement(self, ctx:CompiscriptParser.ForeachStatementContext):

        array_addr = self.visit(ctx.expression())
        array_type = self._get_type_from_addr(array_addr, ctx.expression())

        num_elements = 3 # Asumimos la longitud del array [10, 20, 30]
        element_size = 8 # Asumimos tamaño de integer
        
        index_temp = self.tac.new_temp()
        self.tac.add_instruction('=', '0', None, index_temp) # _index = 0;

        start_label = self.new_label()
        end_label = self.new_label()

        self.tac.add_instruction(op=start_label + ':')

        cond_temp = self.tac.new_temp()
        self.tac.add_instruction('<', index_temp, str(num_elements), cond_temp)
        self.tac.add_instruction('IF_FALSE', cond_temp, None, end_label)

        self.symbol_table.enter_scope()

        offset_temp = self.tac.new_temp()
        self.tac.add_instruction('*', index_temp, str(element_size), offset_temp)
        addr_temp = self.tac.new_temp()
        self.tac.add_instruction('+', array_addr, offset_temp, addr_temp)

        current_element_val = self.tac.new_temp()
        self.tac.add_instruction('=', f"[{addr_temp}]", None, current_element_val)

        loop_var_name = ctx.Identifier().getText()
        loop_var_symbol = VariableSymbol(id=loop_var_name, data_type=array_type.element_type, size=element_size)
        self.symbol_table.add(loop_var_symbol) # Esto le asignará un offset.

        loop_var_addr = f"[BP+{loop_var_symbol.offset}]"
        self.tac.add_instruction('=', current_element_val, None, loop_var_addr)

        self.visit(ctx.block())

        inc_temp = self.tac.new_temp()
        self.tac.add_instruction('+', index_temp, '1', inc_temp)
        self.tac.add_instruction('=', inc_temp, None, index_temp) # index = index + 1;

        self.tac.add_instruction('GOTO', None, None, start_label)

        self.tac.add_instruction(op=end_label + ':')
        self.symbol_table.exit_scope()

        return None


    # Visit a parse tree produced by CompiscriptParser#breakStatement.
    def visitBreakStatement(self, ctx:CompiscriptParser.BreakStatementContext):
        if self.loop_end_labels:
            end_label = self.loop_end_labels[-1]
            self.tac.add_instruction(op='GOTO', result=end_label)
        
        return None


    # Visit a parse tree produced by CompiscriptParser#continueStatement.
    def visitContinueStatement(self, ctx:CompiscriptParser.ContinueStatementContext):
        if self.loop_start_labels:
            start_label = self.loop_start_labels[-1]
            self.tac.add_instruction(op='GOTO', result=start_label)
        return None


    # Visit a parse tree produced by CompiscriptParser#returnStatement.
    def visitReturnStatement(self, ctx:CompiscriptParser.ReturnStatementContext):
        if ctx.expression():
            return_addr = self.visit(ctx.expression())
            self.tac.add_instruction(op='RETURN', arg1=return_addr)
        else:
            
            self.tac.add_instruction(op='RETURN')
        return None


    # Visit a parse tree produced by CompiscriptParser#tryCatchStatement.
    def visitTryCatchStatement(self, ctx:CompiscriptParser.TryCatchStatementContext):

        catch_label = self.new_label()
        end_label = self.new_label()

        self.tac.add_instruction(op='TRY_BEGIN', arg1=catch_label)
        self.visit(ctx.block(0))
        self.tac.add_instruction(op='TRY_END')
        self.tac.add_instruction(op='GOTO', result=end_label)
        self.tac.add_instruction(op=catch_label + ':')
        self.symbol_table.enter_scope()
        
        exception_var_name = ctx.Identifier().getText()
        symbol = self.symbol_table.find(exception_var_name)

        if symbol:
            pass

        self.visit(ctx.block(1))
        self.symbol_table.exit_scope()
        self.tac.add_instruction(op=end_label + ':')

        return None


    # Visit a parse tree produced by CompiscriptParser#switchStatement.
    def visitSwitchStatement(self, ctx:CompiscriptParser.SwitchStatementContext):

        switch_addr = self.visit(ctx.expression())


        case_labels = [self.new_label() for _ in ctx.switchCase()]
        default_label = self.new_label() if ctx.defaultCase() else None
        end_label = self.new_label()

        self.loop_end_labels.append(end_label) 

        for i, case_ctx in enumerate(ctx.switchCase()):

            case_addr = self.visit(case_ctx.expression())
            cond_temp = self.tac.new_temp()
            self.tac.add_instruction('==', switch_addr, case_addr, cond_temp)
            self.tac.add_instruction('IF_TRUE', cond_temp, None, case_labels[i])

        if default_label:
            self.tac.add_instruction('GOTO', None, None, default_label)
        else: 
            self.tac.add_instruction('GOTO', None, None, end_label)

        for i, case_ctx in enumerate(ctx.switchCase()):
            self.tac.add_instruction(op=case_labels[i] + ':')
            for stmt in case_ctx.statement():
                self.visit(stmt)

        if default_label:
            self.tac.add_instruction(op=default_label + ':')
            for stmt in ctx.defaultCase().statement():
                self.visit(stmt)

        self.tac.add_instruction(op=end_label + ':')
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
        func_name = ctx.Identifier().getText()

        self.tac.add_instruction(op=f'{func_name}:')
        self.tac.add_instruction(op='BEGIN_FUNC')
        self.symbol_table.enter_scope()
        
        if self.current_class:
            this_symbol = VariableSymbol(id='this', data_type=self.current_class, size=8, role='Parameter', offset=0)
            self.symbol_table.add(this_symbol)
            
            full_method_name = f"{self.current_class}.{func_name}" if func_name != "constructor" else func_name
            method_symbol = self.symbol_table.find(full_method_name)

            if method_symbol and isinstance(method_symbol.data_type, FunctionType):
                param_offset_start = 8 

                for i, param in enumerate(method_symbol.parameters):
                    param.offset = param_offset_start + (i * 8) # Asumiendo tamaño 8
                    self.symbol_table.add(param)

        self.visit(ctx.block())
        self.symbol_table.exit_scope()

        self.tac.add_instruction(op='END_FUNC')
        return None


    # Visit a parse tree produced by CompiscriptParser#parameters.
    def visitParameters(self, ctx:CompiscriptParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameter.
    def visitParameter(self, ctx:CompiscriptParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classDeclaration.
    def visitClassDeclaration(self, ctx:CompiscriptParser.ClassDeclarationContext):
        class_name = ctx.Identifier(0).getText()
        class_type_row = self.type_table.find(class_name)

        if not class_type_row: return
        
        previous_class = self.current_class
        self.current_class = class_type_row.data_type

        self.symbol_table.enter_scope()

        for member in ctx.classMember():
            if member.functionDeclaration():
                self.visit(member)

        self.symbol_table.exit_scope()
        self.current_class = previous_class # Restauramos el estado

        return None


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

        if len(ctx.expression()) == 0:
            return self.visit(ctx.logicalOrExpr())


        result_addr = self.tac.new_temp()

        false_label = self.new_label()
        end_label = self.new_label()

        condition_addr = self.visit(ctx.logicalOrExpr())

        self.tac.add_instruction('IF_FALSE', condition_addr, None, false_label)

        true_addr = self.visit(ctx.expression(0))
        self.tac.add_instruction('=', true_addr, None, result_addr)

        self.tac.add_instruction('GOTO', None, None, end_label)

        self.tac.add_instruction(op=false_label + ':')
        false_addr = self.visit(ctx.expression(1))
        self.tac.add_instruction('=', false_addr, None, result_addr)

        self.tac.add_instruction(op=end_label + ':')

        return result_addr


    # Visit a parse tree produced by CompiscriptParser#logicalOrExpr.
    def visitLogicalOrExpr(self, ctx:CompiscriptParser.LogicalOrExprContext):
        operands = ctx.logicalAndExpr() 

        if len(operands) == 1:
            return self.visit(operands[0])

        left_addr = self.visit(operands[0])
        right_addr = self.visit(operands[1])
        result_addr = self.tac.new_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_instruction(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#logicalAndExpr.
    def visitLogicalAndExpr(self, ctx:CompiscriptParser.LogicalAndExprContext):
        operands = ctx.equalityExpr() 

        if len(operands) == 1:
            return self.visit(operands[0])

        left_addr = self.visit(operands[0])
        right_addr = self.visit(operands[1])
        result_addr = self.tac.new_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_instruction(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#equalityExpr.
    def visitEqualityExpr(self, ctx:CompiscriptParser.EqualityExprContext):
        operands = ctx.relationalExpr() 
        if len(operands) == 1:
            return self.visit(operands[0])

        left_addr = self.visit(operands[0])
        right_addr = self.visit(operands[1])
        result_addr = self.tac.new_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_instruction(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#relationalExpr.
    def visitRelationalExpr(self, ctx:CompiscriptParser.RelationalExprContext):

        if len(ctx.additiveExpr()) == 1:
            return self.visit(ctx.additiveExpr(0))

        left_addr = self.visit(ctx.additiveExpr(0))
        right_addr = self.visit(ctx.additiveExpr(1))
        result_addr = self.tac.new_temp()
        op = ctx.getChild(1).getText()
        
        self.tac.add_instruction(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#additiveExpr.
    def visitAdditiveExpr(self, ctx:CompiscriptParser.AdditiveExprContext):
        
        if len(ctx.multiplicativeExpr()) == 1:
            return self.visit(ctx.multiplicativeExpr(0))

        
        left_addr = self.visit(ctx.multiplicativeExpr(0))
        right_addr = self.visit(ctx.multiplicativeExpr(1))
        result_addr = self.tac.new_temp() # Devuelve "t0"
        op = ctx.getChild(1).getText() # Obtiene "+"
        
        self.tac.add_instruction(op, left_addr, right_addr, result_addr)

        return result_addr


    # Visit a parse tree produced by CompiscriptParser#multiplicativeExpr.
    def visitMultiplicativeExpr(self, ctx:CompiscriptParser.MultiplicativeExprContext):
        
        if len(ctx.unaryExpr()) == 1:
            return self.visit(ctx.unaryExpr(0))
        
        left_addr = self.visit(ctx.unaryExpr(0))
        right_addr = self.visit(ctx.unaryExpr(1))
        result_addr = self.tac.new_temp()
        op = ctx.getChild(1).getText()
        self.tac.add_instruction(op, left_addr, right_addr, result_addr)
        
        return result_addr


    # Visit a parse tree produced by CompiscriptParser#unaryExpr.
    def visitUnaryExpr(self, ctx:CompiscriptParser.UnaryExprContext):
        
        if ctx.primaryExpr():
            return self.visit(ctx.primaryExpr())
        
        operand_addr = self.visit(ctx.unaryExpr())
        op = ctx.getChild(0).getText()
        result_addr = self.tac.new_temp()
        
        if op == '-':
            self.tac.add_instruction(op, '0', operand_addr, result_addr)
        elif op == '!':
            self.tac.add_instruction('==', operand_addr, 'false', result_addr)
        
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
    def visitLeftHandSide(self, ctx:CompiscriptParser.LeftHandSideContext):
        
        current_addr = self.visit(ctx.primaryAtom())
        current_type = self._get_type_from_addr(current_addr, ctx.primaryAtom())
        
        for suffix in ctx.suffixOp():
            
            if isinstance(current_type, ErrorType): 
                return ErrorType()
            
            if isinstance(suffix, CompiscriptParser.CallExprContext):
                arg_addrs = []
                if suffix.arguments():
                
                    for arg_expr in suffix.arguments().expression():
                        arg_addr = self.visit(arg_expr)
                        self.tac.add_instruction(op='PARAM', arg1=arg_addr)
                        arg_addrs.append(arg_addr)
                
                result_addr = self.tac.new_temp()
                num_args = len(arg_addrs)

                self.tac.add_instruction(op='CALL', arg1=current_addr, arg2=str(num_args), result=result_addr)
                current_addr = result_addr
                
                if isinstance(current_type, FunctionType):
                    current_type = current_type.return_type

            elif isinstance(suffix, CompiscriptParser.PropertyAccessExprContext):
                prop_name = suffix.Identifier().getText()
                
                if isinstance(current_type, ClassType):
                    class_name = str(current_type)
                    class_type_row = self.type_table.find(class_name)
                    
                    if class_type_row and prop_name in class_type_row.attributes:
                        prop_type = class_type_row.attributes[prop_name]
                        
                        if isinstance(prop_type, FunctionType):
                            current_addr = f"{class_name}.{prop_name}"
                        else:
                            prop_offset = 0 
                            prop_addr = f"[{current_addr}+{prop_offset}]"
                            value_temp = self.tac.new_temp()
                            self.tac.add_instruction('=', prop_addr, None, value_temp)
                            current_addr = value_temp
                        current_type = prop_type

            elif isinstance(suffix, CompiscriptParser.IndexExprContext):
                if isinstance(current_type, ArrayType):
                    index_addr = self.visit(suffix.expression())
                    element_type = current_type.element_type
                    type_row = self.type_table.find(str(element_type))
                    element_size = str(type_row.size) if type_row else "8" # Usamos 8 como fallback
                    offset_temp = self.tac.new_temp()

                    self.tac.add_instruction('*', index_addr, element_size, offset_temp)
        
                    final_addr_temp = self.tac.new_temp()
                    self.tac.add_instruction('+', current_addr, offset_temp, final_addr_temp)
        
                    value_temp = self.tac.new_temp()
                    self.tac.add_instruction('=', f"[{final_addr_temp}]", None, value_temp)
        
                    current_addr = value_temp
                    current_type = element_type

        return current_addr


    # Visit a parse tree produced by CompiscriptParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:CompiscriptParser.IdentifierExprContext):
        var_name = ctx.getText()
        symbol = self.symbol_table.find(var_name)
        
        if symbol and hasattr(symbol, 'offset') and symbol.offset is not None:
            return f"[BP+{symbol.offset}]"
        
        return var_name


    # Visit a parse tree produced by CompiscriptParser#NewExpr.
    def visitNewExpr(self, ctx:CompiscriptParser.NewExprContext):
        class_name = ctx.Identifier().getText()
        num_args = 0
        if ctx.arguments():
            num_args = len(ctx.arguments().expression())
            for arg_expr in ctx.arguments().expression():
                arg_addr = self.visit(arg_expr)
                self.tac.add_instruction(op='PARAM', arg1=arg_addr)
        
        result_addr = self.tac.new_temp()

        self.tac.add_instruction(op='NEW', arg1=class_name, arg2=str(num_args), result=result_addr)

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


        base_addr = self.tac.new_temp()

        self.tac.add_instruction(op='ALLOCATE', arg1=str(total_size), result=base_addr)

        current_offset = 0
        for addr in element_addrs:

            dest_addr = f"[{base_addr}+{current_offset}]"
            self.tac.add_instruction('=', addr, None, dest_addr)
            current_offset += element_size

        return base_addr


    # Visit a parse tree produced by CompiscriptParser#type.
    def visitType(self, ctx:CompiscriptParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#baseType.
    def visitBaseType(self, ctx:CompiscriptParser.BaseTypeContext):
        return self.visitChildren(ctx)

