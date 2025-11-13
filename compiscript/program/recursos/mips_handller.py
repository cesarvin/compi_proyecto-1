class MipsHandler:
    def __init__(self, tac_code, symbol_table, type_table):
            self.tac_code = tac_code
            self.symbol_table = symbol_table
            self.type_table = type_table

            self.data_section = [".data"]
            self.text_section = [
                    ".text",
                    ".globl main",
                    "main:"
            ]

            self.available_registers = [f"$t{i}" for i in range(10)]

            self.temp_register_map = {}

    def get_registro(self, tac_temp):
            if tac_temp in self.temp_register_map:
                    return self.temp_register_map[tac_temp]
            
            if not self.available_registers:
                    raise Exception("¡Error del compilador! No hay más registros disponibles.")
                    
            mips_reg = self.available_registers.pop(0) 
            self.temp_register_map[tac_temp] = mips_reg
            return mips_reg

    def liberar_registro(self, tac_temp):
            if tac_temp in self.temp_register_map:
                    mips_reg = self.temp_register_map.pop(tac_temp) 
                    self.available_registers.append(mips_reg) 

    
    def _es_temporal(self, addr):
        return addr and addr.startswith('t')

    def _es_memoria(self, addr):
        return addr and addr.startswith('[')

    def _get_offset(self, mem_addr):
        try:
            return int(mem_addr.replace('[BP+', '').replace(']', ''))
        except ValueError:
            print(f"Advertencia: No se pudo parsear el offset de {mem_addr}")
            return 0

    
    def _traducir_asignacion(self, quad):
        fuente = quad.arg1
        destino = quad.result

        
        if self._es_temporal(destino) and not self._es_temporal(fuente) and not self._es_memoria(fuente):
            reg_destino = self.get_registro(destino)
            self.text_section.append(f"  li {reg_destino}, {fuente}") # li = Load Immediate

        elif self._es_temporal(destino) and self._es_memoria(fuente):
            reg_destino = self.get_registro(destino)
            offset = self._get_offset(fuente)
            self.text_section.append(f"  lw {reg_destino}, {offset}($fp)") # lw = Load Word
        
        elif self._es_memoria(destino) and self._es_temporal(fuente):
            reg_fuente = self.get_registro(fuente)
            offset = self._get_offset(destino)
            self.text_section.append(f"  sw {reg_fuente}, {offset}($fp)") # sw = Store Word
        
        elif self._es_memoria(destino) and not self._es_temporal(fuente) and not self._es_memoria(fuente):
            offset = self._get_offset(destino)
            
            self.text_section.append(f"  li $v1, {fuente}") 
            self.text_section.append(f"  sw $v1, {offset}($fp)")

        elif self._es_temporal(destino) and self._es_temporal(fuente):
            reg_destino = self.get_registro(destino)
            reg_fuente = self.get_registro(fuente)
            self.text_section.append(f"  move {reg_destino}, {reg_fuente}")

    def _traducir_suma(self, quad):
        
        reg_arg1 = self.get_registro(quad.arg1)
        reg_arg2 = self.get_registro(quad.arg2)
        reg_result = self.get_registro(quad.result)
        
        self.text_section.append(f"  add {reg_result}, {reg_arg1}, {reg_arg2}")
        
        if self._es_temporal(quad.arg1):
            self.liberar_registro(quad.arg1)
        if self._es_temporal(quad.arg2):
            self.liberar_registro(quad.arg2)

    
    def generar_codigo(self):
            self.text_section.append("  move $fp, $sp") 
            
            for quad in self.tac_code:
                    self.text_section.append(f"\n  # TAC: {quad}")
                    
                    if quad.op == '=':
                        self._traducir_asignacion(quad)
                    
                    elif quad.op == '+':
                        self._traducir_suma(quad)
            
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