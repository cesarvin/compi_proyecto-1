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


    def _es_temporal(self, addr):
        return addr and (addr.startswith('t') or addr.startswith('_internal_t'))

    def _es_memoria(self, addr):
        return addr and addr.startswith('[')

    def _get_offset(self, mem_addr):
        try:
            return int(mem_addr.replace('[BP+', '').replace(']', ''))
        except ValueError:
            print(f"No se pudo parsear el offset de {mem_addr}")
            return 0

    def _new_internal_temp(self):
        temp_name = f"_internal_t{self.internal_temp_counter}"
        self.internal_temp_counter += 1
        return temp_name

    def _get_operand_register(self, operand):
        if self._es_temporal(operand):
            return self.get_registro(operand)
        
        elif self._es_memoria(operand):
            reg = self.get_registro(self._new_internal_temp())
            offset = self._get_offset(operand)
            self.text_section.append(f"  lw {reg}, {offset}($fp)")
            return reg
        
        else:
            reg = self.get_registro(self._new_internal_temp())
            self.text_section.append(f"  li {reg}, {operand}")
            return reg

    def _get_string_label(self, string_literal):
        str_val = string_literal.strip('"')
        
        if str_val in self.string_map:
            return self.string_map[str_val]
        
        label = f"str{self.string_counter}"
        self.string_counter += 1
        self.string_map[str_val] = label
        self.data_section.append(f"  {label}: .asciiz \"{str_val}\"")
        
        return label

    def _traducir_asignacion(self, quad):
        fuente = quad.arg1
        destino = quad.result
        
        if self._es_temporal(destino) and not self._es_temporal(fuente) and not self._es_memoria(fuente):
            reg_destino = self.get_registro(destino)
            self.text_section.append(f"  li {reg_destino}, {fuente}")
        
        elif self._es_temporal(destino) and self._es_memoria(fuente):
            reg_destino = self.get_registro(destino)
            offset = self._get_offset(fuente)
            self.text_section.append(f"  lw {reg_destino}, {offset}($fp)")
        
        elif self._es_memoria(destino) and self._es_temporal(fuente):
            reg_fuente = self.get_registro(fuente)
            offset = self._get_offset(destino)
            self.text_section.append(f"  sw {reg_fuente}, {offset}($fp)")
        
        elif self._es_memoria(destino) and not self._es_temporal(fuente) and not self._es_memoria(fuente):
            offset = self._get_offset(destino)
        
            if quad.arg1.startswith('"'):
                label = self._get_string_label(quad.arg1)
                self.text_section.append(f"  la $v1, {label}") 
            else:
                self.text_section.append(f"  li $v1, {fuente}") 
        
            self.text_section.append(f"  sw $v1, {offset}($fp)")
        
        elif self._es_temporal(destino) and self._es_temporal(fuente):
            reg_destino = self.get_registro(destino)
            reg_fuente = self.get_registro(fuente)
            self.text_section.append(f"  move {reg_destino}, {reg_fuente}")


    def _traducir_suma(self, quad):
        reg_arg1 = self._get_operand_register(quad.arg1)
        reg_arg2 = self._get_operand_register(quad.arg2)
        reg_result = self.get_registro(quad.result)
        self.text_section.append(f"  add {reg_result}, {reg_arg1}, {reg_arg2}")
        
        if self._es_temporal(quad.arg1): 
            self.liberar_registro(quad.arg1)
        
        if self._es_temporal(quad.arg2):
            self.liberar_registro(quad.arg2)

    def _traducir_resta(self, quad):
        reg_arg1 = self._get_operand_register(quad.arg1)
        reg_arg2 = self._get_operand_register(quad.arg2)
        reg_result = self.get_registro(quad.result)
        self.text_section.append(f"  sub {reg_result}, {reg_arg1}, {reg_arg2}")
        
        if self._es_temporal(quad.arg1):
            self.liberar_registro(quad.arg1)
        
        if self._es_temporal(quad.arg2):
            self.liberar_registro(quad.arg2)

    def _traducir_mult(self, quad):
        reg_arg1 = self._get_operand_register(quad.arg1)
        reg_arg2 = self._get_operand_register(quad.arg2)
        reg_result = self.get_registro(quad.result)
        
        self.text_section.append(f"  mult {reg_arg1}, {reg_arg2}")
        self.text_section.append(f"  mflo {reg_result}")
        
        if self._es_temporal(quad.arg1): 
            self.liberar_registro(quad.arg1)
        
        if self._es_temporal(quad.arg2): 
            self.liberar_registro(quad.arg2)

    def _traducir_div(self, quad):
        reg_arg1 = self._get_operand_register(quad.arg1)
        reg_arg2 = self._get_operand_register(quad.arg2)
        reg_result = self.get_registro(quad.result)
        
        self.text_section.append(f"  div {reg_arg1}, {reg_arg2}")
        self.text_section.append(f"  mflo {reg_result}")
        
        if self._es_temporal(quad.arg1):
            self.liberar_registro(quad.arg1)
        
        if self._es_temporal(quad.arg2):
            self.liberar_registro(quad.arg2)

    def _traducir_etiqueta(self, quad):
        self.text_section.append(f"{quad.op}")

    def _traducir_goto(self, quad):
        self.text_section.append(f"  j {quad.result}")

    def _traducir_relacional(self, quad):
        op = quad.op
        reg_arg1 = self._get_operand_register(quad.arg1)
        reg_arg2 = self._get_operand_register(quad.arg2)
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
        
        if self._es_temporal(quad.arg1): 
            self.liberar_registro(quad.arg1)
        
        if self._es_temporal(quad.arg2): 
            self.liberar_registro(quad.arg2)

    def _traducir_if_false(self, quad):
        reg_condicion = self.get_registro(quad.arg1)
        etiqueta_destino = quad.result
        self.text_section.append(f"  beq {reg_condicion}, $zero, {etiqueta_destino}")
        
        if self._es_temporal(quad.arg1): 
            self.liberar_registro(quad.arg1)

    def _traducir_if_true(self, quad):
        reg_condicion = self.get_registro(quad.arg1)
        etiqueta_destino = quad.result
        self.text_section.append(f"  bne {reg_condicion}, $zero, {etiqueta_destino}")
        if self._es_temporal(quad.arg1): 
            self.liberar_registro(quad.arg1)

    def _traducir_param(self, quad):
        param = quad.arg1
        
        if param.startswith('"'):
            label = self._get_string_label(param)
            self.text_section.append(f"  la $a0, {label}") 
            self.last_param_type = 'string'
        
        else:
            reg_param = self._get_operand_register(param)
            self.text_section.append(f"  move $a0, {reg_param}")
            self.last_param_type = 'int'
        
            if self._es_temporal(param):
                self.liberar_registro(param)

    def _traducir_call(self, quad):
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
            self.text_section.append(f"  jal {func_name}") 
        
        
        if quad.result:
            reg_result = self.get_registro(quad.result)
            self.text_section.append(f"  move {reg_result}, $v0")


    def _traducir_begin_func(self, quad):
        self.text_section.append("  # --- Prólogo de Función ---")
        self.text_section.append("  sw $ra, -4($sp)")
        self.text_section.append("  sw $fp, -8($sp)")
        self.text_section.append("  addiu $sp, $sp, -8")
        self.text_section.append("  move $fp, $sp")
        self.text_section.append("  addiu $sp, $sp, -128") 
        self.text_section.append("  sw $a0, 8($fp)")
        self.text_section.append("  sw $a1, 16($fp)")
        self.text_section.append("  sw $a2, 24($fp)") 
        self.text_section.append("  sw $a3, 32($fp)")



    def _traducir_return(self, quad):
        self.text_section.append("  # --- Epílogo de Función (Return) ---")

        if quad.arg1:
            reg_ret_val = self._get_operand_register(quad.arg1)
            self.text_section.append(f"  move $v0, {reg_ret_val}")

        self.text_section.append("  move $sp, $fp") 
        self.text_section.append("  lw $fp, 0($sp)")
        self.text_section.append("  lw $ra, 4($sp)")
        self.text_section.append("  addiu $sp, $sp, 8")
        self.text_section.append("  jr $ra") 

    def _traducir_end_func(self, quad):
        self.text_section.append("  # --- Epílogo de Función (End) ---")
        self.text_section.append("  move $sp, $fp")
        self.text_section.append("  lw $fp, 0($sp)")
        self.text_section.append("  lw $ra, 4($sp)")
        self.text_section.append("  addiu $sp, $sp, 8")
        self.text_section.append("  jr $ra")



    def generar_codigo(self):
        self.text_section.append("  move $fp, $sp") 
        self.text_section.append("  addiu $sp, $sp, -128")
        
        self.text_section.append("  j main_body_start")
        
        first_main_instruction = True
        
        for quad in self.tac_code:
                self.text_section.append(f"\n  # TAC: {quad}")
            
                if quad.op.endswith(':'):
                    if not quad.op.startswith('_'): 
                        self.dentro_de_funcion = True

                elif quad.op == 'END_FUNC':
                    self.dentro_de_funcion = False
            
                is_main_instruction = not self.dentro_de_funcion
            
                if first_main_instruction and is_main_instruction and quad.op != 'END_FUNC':
                    self.text_section.append("main_body_start:")
                    first_main_instruction = False

                if quad.op == '=': 
                    self._traducir_asignacion(quad)
                
                elif quad.op in ['+', '-', '*', '/']:
                    if quad.op == '+': self._traducir_suma(quad)
                    if quad.op == '-': self._traducir_resta(quad)
                    if quad.op == '*': self._traducir_mult(quad)
                    if quad.op == '/': self._traducir_div(quad)
                
                elif quad.op in ['<', '>', '==', '!=', '<=', '>=']:
                    self._traducir_relacional(quad)
                
                elif quad.op == 'IF_FALSE': 
                    self._traducir_if_false(quad)
                
                elif quad.op == 'IF_TRUE':
                    self._traducir_if_true(quad)
                
                elif quad.op == 'PARAM':
                    self._traducir_param(quad)
                
                elif quad.op == 'CALL':
                    self._traducir_call(quad)
                
                elif quad.op == 'BEGIN_FUNC':
                    self._traducir_begin_func(quad)
                
                elif quad.op == 'RETURN':
                    self._traducir_return(quad)
                
                elif quad.op == 'END_FUNC':
                    self._traducir_end_func(quad)
                
                elif quad.op.endswith(':'):
                    self._traducir_etiqueta(quad)
                
                elif quad.op == 'GOTO':
                    self._traducir_goto(quad)
        
        self.end_program()
        return self.get_mips_code()



    def end_program(self):
        self.text_section.append("\n  # --- Salir del Programa ---")
        self.text_section.append("  li $v0, 10  ")
        self.text_section.append("  syscall")

    def get_mips_code(self):
        data = "\n".join(self.data_section)
        text = "\n".join(self.text_section)
        return f"{data}\n\n{text}"