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
        
    def __str__(self):
        return (f"{str(self.id):<15} {str(self.data_type):<15} "
                f"{str(self.size):<5} {str(self.scope):<5} "
                f"{str(self.parent_scope):<10} {str(self.p_class):<10} "
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
        self.type_table = type_table  # tabla de tipos
        self.scopes = [{}]  # stack de ámbitos, cada ámbito es un diccionario

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
        
        print("\n" + "=" * 43 + " SYMBOL TABLE " + "=" * 43)
        header = (f"{'ID':<15} "
                  f"{'TYPE':<15} "
                  f"{'SIZE':<5} "
                  f"{'SCOPE':<5} "
                  f"{'PARENT_S':<10} "
                  f"{'CLASS':<10} "
                  f"{'FUNCTION':<10} "
                  f"{'ROLE':<10}")
        
        print(header)
        print("-" * 100)

        for level, scope in enumerate(self.scopes, 1):
            if not scope: 
                continue
            
            print(" " * 46 + f" Ámbito {level} " + " " * 46)
            
            for symbol in scope.values():
                print(symbol)
        
        
        print("\n" + "=" * 100 + "\n")