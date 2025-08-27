class SymbolRow:
    #def __init__(self, id, data_type, size = 0, offset = 0, scope = None, p_class = None, p_function = None, is_param = False):
    def __init__(self, id, data_type, size = 0, scope = None, parent_scope = None, p_class = None, p_function = None, is_param = 'Parameter'):
        self.id = id
        self.data_type = data_type
        self.size = size
        #self.offset = offset
        self.scope = scope
        self.parent_scope = parent_scope
        self.p_class = p_class
        self.p_function = p_function
        self.is_param = is_param
        
    # def __str__(self):
    #     return '{0} {1} {2} {3} {4} {5} {6} {7}'.format(self.id, self.data_type, self.size, self.scope, self.parent_scope, self.p_class, self.p_function, self.is_param)
    def __str__(self):
        return (f"{str(self.id):<15} {str(self.data_type):<15} {str(self.size):<5} "
                f"{str(self.scope):<5} {str(self.parent_scope):<10} {str(self.p_class):<10} "
                f"{str(self.p_function):<10} {str(self.is_param):<10}")

    def to_dict(self):
        return {
            'id': self.id,
            'data_type': self.data_type,
            'size': self.size,
            'scope': self.scope,
            'parent_scope': self.parent_scope,
            'p_class': self.p_class,
            'p_function': self.p_function,
            'is_param': self.is_param
        }

   
class SymbolTable:
    def __init__(self, type_table):
        self.type_table = type_table  
        self.scopes = [{}]  

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add(self, symbol_row):
        current_scope = self.scopes[-1]
        if symbol_row.id in current_scope:
            return False
        current_scope[symbol_row.id] = symbol_row
        return True

    def find(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None 

    def get_current_scope_level(self):
        return len(self.scopes)
    
    def find_in_current_scope(self, name):
        current_scope = self.scopes[-1]
        return current_scope.get(name)

    def print_table(self):
        """
        Imprime la tabla de símbolos completa, mostrando los diferentes ámbitos.
        """
        print("\n===== SYMBOL TABLE =====")
        header = (f"{'ID':<15} {'TYPE':<15} {'SIZE':<5} "
                  f"{'SCOPE':<5} {'PARENT_S':<10} {'CLASS':<10} "
                  f"{'FUNCTION':<10} {'ROLE':<10}")
        print(header)
        print("-" * 95)

        # Itera sobre cada ámbito (diccionario) en la pila de ámbitos
        for level, scope in enumerate(self.scopes, 1):
            if not scope: # Si el ámbito está vacío, no imprimas nada para él
                continue
            
            print(f"--- Ámbito Nivel {level} ---")
            # Itera sobre cada símbolo (objeto SymbolRow) en el diccionario del ámbito actual
            for symbol in scope.values():
                # Python llama automáticamente a symbol.__str__()
                print(symbol)
        
        print("========================\n")