class MipsHandler:

    def __init__(self, tac_code, symbol_table, type_table):
        self.tac_code = tac_code
        self.symbol_table = symbol_table
        self.type_table = type_table
        self.data_section = [".data"]
        self.text_section = [".text", ".globl main", "main:"]
        self.available_registers = [f"$t{i}" for i in range(10)]
        self.temp_register_map = {}
        self.internal_temp_counter = 0 
        self.string_map = {} 
        self.string_counter = 0 
        self.last_param_type = None 
        self.dentro_de_funcion = False


    def get_registro(self, tac_temp):
        if tac_temp in self.temp_register_map:
            return self.temp_register_map[tac_temp]

        if not self.available_registers:
            raise Exception("Ocurrió un error. No hay más registros disponibles.")

        mips_reg = self.available_registers.pop(0) 
        self.temp_register_map[tac_temp] = mips_reg
        
        return mips_reg


    def liberar_registro(self, tac_temp):
        if tac_temp in self.temp_register_map:
            mips_reg = self.temp_register_map.pop(tac_temp) 
            self.available_registers.append(mips_reg) 


    def es_temporal(self, addr):
        return addr and (addr.startswith('t') or addr.startswith('_internal_t'))

    def es_memoria(self, addr):
        return addr and addr.startswith('[')

    def get_offset(self, mem_addr):
        try:
            return int(mem_addr.replace('[BP+', '').replace(']', ''))
        except ValueError:
            print(f"No se pudo parsear el offset de {mem_addr}")
            return 0

    def new_temp_i(self):
        temp_name = f"_internal_t{self.internal_temp_counter}"
        self.internal_temp_counter += 1
        return temp_name

    
    def get_op(self, operand):
        if self.es_temporal(operand):
            return self.get_registro(operand), operand
        
        elif self.es_memoria(operand):
            if 'BP' in operand:
                temp = self.new_temp_i()
                reg = self.get_registro(temp)
                offset = self.get_offset(operand)
                self.text_section.append(f"  lw {reg}, {offset}($fp)")
                return reg, temp
            else:
                
                content = operand.strip('[]')
                if '+' in content:
                    base, off = content.split('+')
                    offset = int(off)
                else:
                    base = content
                    offset = 0
                
                reg_base = self.get_registro(base)
                temp = self.new_temp_i()
                reg_dest = self.get_registro(temp)
                
                self.text_section.append(f"  lw {reg_dest}, {offset}({reg_base})")
                
                
                if self.es_temporal(base):
                    self.liberar_registro(base)
                
                
                return reg_dest, temp
        
        else: # Literales
            temp = self.new_temp_i()
            reg = self.get_registro(temp)
            self.text_section.append(f"  li {reg}, {operand}")
            return reg, temp

    def get_label(self, string_literal):
        str_val = string_literal.strip('"')
        
        if str_val in self.string_map:
            return self.string_map[str_val]
        
        label = f"str{self.string_counter}"
        self.string_counter += 1
        self.string_map[str_val] = label
        self.data_section.append(f"  {label}: .asciiz \"{str_val}\"")
        
        return label

    
    def traduce_asignar(self, quad):
        reg_fuente = None
        temp_fuente = None
        es_string = False

        if str(quad.arg1).startswith('"'):
            label = self.get_label(quad.arg1)
            temp_fuente = self.new_temp_i()
            reg_fuente = self.get_registro(temp_fuente)
            self.text_section.append(f"  la {reg_fuente}, {label}")
            es_string = True
        else:
            reg_fuente, temp_fuente = self.get_op(quad.arg1)

        destino = quad.result
        
        if self.es_temporal(destino):
            reg_destino = self.get_registro(destino)
            self.text_section.append(f"  move {reg_destino}, {reg_fuente}")

        elif self.es_memoria(destino):
            
            if 'BP' in destino:
                offset = self.get_offset(destino)
                self.text_section.append(f"  sw {reg_fuente}, {offset}($fp)")
            else:
                
                content = destino.strip('[]')
                if '+' in content:
                    base_temp, off_str = content.split('+')
                    offset = int(off_str)
                else:
                    base_temp = content
                    offset = 0
                
                reg_base = self.get_registro(base_temp)
                
                self.text_section.append(f"  sw {reg_fuente}, {offset}({reg_base})")

                
                # if self.es_temporal(base_temp):
                #     self.liberar_registro(base_temp)
                

        if temp_fuente:
            self.liberar_registro(temp_fuente)


    def traduce_allocate(self, quad):
        reg_size, temp_size = self.get_op(quad.arg1)
        self.text_section.append(f"  move $a0, {reg_size}")
        
        self.text_section.append("  li $v0, 9")
        self.text_section.append("  syscall")
        
        reg_result = self.get_registro(quad.result)
        self.text_section.append(f"  move {reg_result}, $v0")
        
        if temp_size: self.liberar_registro(temp_size)

    def traduce_new(self, quad):
        self.text_section.append("  li $a0, 128") 
        self.text_section.append("  li $v0, 9") 
        self.text_section.append("  syscall")
        
        reg_result = self.get_registro(quad.result)
        self.text_section.append(f"  move {reg_result}, $v0")

    def traduce_suma(self, quad):
        reg_arg1, temp1 = self.get_op(quad.arg1)
        reg_arg2, temp2 = self.get_op(quad.arg2)
        reg_result = self.get_registro(quad.result)
        self.text_section.append(f"  add {reg_result}, {reg_arg1}, {reg_arg2}")
        
        self.liberar_registro(temp1)
        self.liberar_registro(temp2)

    def traduce_resta(self, quad):
        reg_arg1, temp1 = self.get_op(quad.arg1)
        reg_arg2, temp2 = self.get_op(quad.arg2)
        reg_result = self.get_registro(quad.result)
        self.text_section.append(f"  sub {reg_result}, {reg_arg1}, {reg_arg2}")
        
        self.liberar_registro(temp1)
        self.liberar_registro(temp2)

    def traduce_mul(self, quad):
        reg_arg1, temp1 = self.get_op(quad.arg1)
        reg_arg2, temp2 = self.get_op(quad.arg2)
        reg_result = self.get_registro(quad.result)
        
        self.text_section.append(f"  mult {reg_arg1}, {reg_arg2}")
        self.text_section.append(f"  mflo {reg_result}")
        
        self.liberar_registro(temp1)
        self.liberar_registro(temp2)

    def traduce_div(self, quad):
        reg_arg1, temp1 = self.get_op(quad.arg1)
        reg_arg2, temp2 = self.get_op(quad.arg2)
        reg_result = self.get_registro(quad.result)
        
        self.text_section.append(f"  div {reg_arg1}, {reg_arg2}")
        self.text_section.append(f"  mflo {reg_result}")
        
        self.liberar_registro(temp1)
        self.liberar_registro(temp2)

    def traduce_label(self, quad):
        self.text_section.append(f"{quad.op}")

    def traduce_goto(self, quad):
        self.text_section.append(f"  j {quad.result}")

    def traduce_iguales(self, quad):
        op = quad.op
        reg_arg1, temp1 = self.get_op(quad.arg1)
        reg_arg2, temp2 = self.get_op(quad.arg2)
        reg_result = self.get_registro(quad.result)
        
        if op == '<': 
            self.text_section.append(f"  slt {reg_result}, {reg_arg1}, {reg_arg2}")
        elif op == '>': 
            self.text_section.append(f"  slt {reg_result}, {reg_arg2}, {reg_arg1}")
        elif op == '==': 
            self.text_section.append(f"  seq {reg_result}, {reg_arg1}, {reg_arg2}")
        elif op == '!=': 
            self.text_section.append(f"  sne {reg_result}, {reg_arg1}, {reg_arg2}")
        elif op == '<=': 
            self.text_section.append(f"  sle {reg_result}, {reg_arg1}, {reg_arg2}")
        elif op == '>=': 
            self.text_section.append(f"  sge {reg_result}, {reg_arg1}, {reg_arg2}")
        
        self.liberar_registro(temp1)
        self.liberar_registro(temp2)

    def traduce_if_false(self, quad):
        reg_cond, temp_cond = self.get_op(quad.arg1)
        etiqueta_destino = quad.result
        self.text_section.append(f"  beq {reg_cond}, $zero, {etiqueta_destino}")
        
        self.liberar_registro(temp_cond)

    def traduce_if_true(self, quad):
        reg_cond, temp_cond = self.get_op(quad.arg1)
        etiqueta_destino = quad.result
        self.text_section.append(f"  bne {reg_cond}, $zero, {etiqueta_destino}")
        self.liberar_registro(temp_cond)

    def traduce_param(self, quad):
        param = quad.arg1
        type_hint = quad.arg2
        if param.startswith('"'):
            label = self.get_label(param)
            self.text_section.append(f"  la $a0, {label}") 
            self.last_param_type = 'string'
        
        else:
            reg_param, temp_param = self.get_op(param)
            self.text_section.append(f"  move $a0, {reg_param}")
            if type_hint == 'string':
                self.last_param_type = 'string'
            else:
                self.last_param_type = 'int'
        
            self.liberar_registro(temp_param)

    def traduce_call(self, quad):
        func_name = quad.arg1
        
        if func_name == 'print':
            if self.last_param_type == 'string':
                self.text_section.append("  li $v0, 4  # syscall: print string")
            else: 
                self.text_section.append("  li $v0, 1  # syscall: print integer")
            self.text_section.append("  syscall")
            self.text_section.append("  li $v0, 11 # syscall: print char (newline)")
            self.text_section.append("  li $a0, 10 # ASCII 10 es ''")
            self.text_section.append("  syscall")
        else:
            
            self.text_section.append("  addiu $sp, $sp, -16") # Reservar espacio
            
            self.text_section.append(f"  jal {func_name}") 
            
            self.text_section.append("  addiu $sp, $sp, 16") # Restaurar espacio
            
        
        if quad.result:
            reg_result = self.get_registro(quad.result)
            self.text_section.append(f"  move {reg_result}, $v0")
        


    def traduce_begin_func(self, quad):
        self.text_section.append("  sw $ra, -4($sp)")
        self.text_section.append("  sw $fp, -8($sp)")
        self.text_section.append("  addiu $sp, $sp, -8")
        self.text_section.append("  move $fp, $sp")
        self.text_section.append("  addiu $sp, $sp, -128") 
        self.text_section.append("  sw $a0, 8($fp)")
        self.text_section.append("  sw $a1, 16($fp)")
        self.text_section.append("  sw $a2, 24($fp)") 
        self.text_section.append("  sw $a3, 32($fp)")


    def traduce_return(self, quad):
        
        if quad.arg1:
            reg_ret, temp_ret = self.get_op(quad.arg1)
            self.text_section.append(f"  move $v0, {reg_ret}")
            self.liberar_registro(temp_ret)

        self.text_section.append("  move $sp, $fp") 
        self.text_section.append("  lw $fp, 0($sp)")
        self.text_section.append("  lw $ra, 4($sp)")
        self.text_section.append("  addiu $sp, $sp, 8")
        self.text_section.append("  jr $ra") 

    def traduce_end_func(self, quad):
        self.text_section.append("  move $sp, $fp")
        self.text_section.append("  lw $fp, 0($sp)")
        self.text_section.append("  lw $ra, 4($sp)")
        self.text_section.append("  addiu $sp, $sp, 8")
        self.text_section.append("  jr $ra")



    def generar_codigo(self):
            self.text_section.append("  move $fp, $sp") 
            self.text_section.append("  addiu $sp, $sp, -128")
            self.text_section.append("  j main_body_start")
            
            function_code = []
            main_code = []
            inside_func = False
            
            for quad in self.tac_code:
                
                if quad.op == 'BEGIN_FUNC':
                    inside_func = True
                    
                    if main_code and main_code[-1].op.endswith(':'):
                        label_quad = main_code.pop()
                        function_code.append(label_quad)

                if inside_func:
                    function_code.append(quad)
                else:
                    main_code.append(quad)
                
                if quad.op == 'END_FUNC':
                    inside_func = False
            
            for quad in function_code:
                self.procesar_tac(quad)

            self.text_section.append("\nmain_body_start:")
            
            for quad in main_code:
                self.procesar_tac(quad)
            
            self.end_program()
            return self.get_mips_code()


    def procesar_tac(self, quad):
        if quad.op == '=': 
            self.traduce_asignar(quad)
        elif quad.op in ['+', '-', '*', '/']:
            if quad.op == '+': 
                self.traduce_suma(quad)
            elif quad.op == '-': 
                self.traduce_resta(quad)
            elif quad.op == '*':
                self.traduce_mul(quad)
            elif quad.op == '/':
                self.traduce_div(quad)
        elif quad.op in ['<', '>', '==', '!=', '<=', '>=']:
            self.traduce_iguales(quad)

        elif quad.op == 'ALLOCATE':
            self.traduce_allocate(quad)

        elif quad.op == 'NEW':
            self.traduce_new(quad)

        elif quad.op == 'IF_FALSE':
            self.traduce_if_false(quad)

        elif quad.op == 'IF_TRUE':
            self.traduce_if_true(quad)

        elif quad.op == 'PARAM':
            self.traduce_param(quad)

        elif quad.op == 'CALL':
            self.traduce_call(quad)

        elif quad.op == 'BEGIN_FUNC':
            self.traduce_begin_func(quad)

        elif quad.op == 'RETURN':
            self.traduce_return(quad)

        elif quad.op == 'END_FUNC':
            self.traduce_end_func(quad)

        elif quad.op.endswith(':'):
            self.traduce_label(quad)

        elif quad.op == 'GOTO': 
            self.traduce_goto(quad)



    def end_program(self):
        self.text_section.append("\n  # --- fin del Programa ---")
        self.text_section.append("  li $v0, 10  ")
        self.text_section.append("  syscall")

    def get_mips_code(self):
        data = "\n".join(self.data_section)
        text = "\n".join(self.text_section)
        return f"{data}\n\n{text}"