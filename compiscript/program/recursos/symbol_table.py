class Symbol:
    def __init__(self, id, data_type, size=0, scope=None, parent_scope=None):
        self.id = id
        self.data_type = data_type
        self.size = size
        self.scope = scope
        self.parent_scope = parent_scope
        
    def __str__(self):
        return f"{self.id:<15} {str(self.data_type):<15} {str(self.size):<5} {str(self.scope):<5}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_type': str(self.data_type),
            'size': self.size,
            'scope': self.scope,
            'parent_scope': self.parent_scope
        }

class VariableSymbol(Symbol):
    def __init__(self, id, data_type, size=0, scope=None, parent_scope=None, p_class=None, p_function=None, role='Variable',  offset=None):
        super().__init__(id, data_type, size, scope, parent_scope)
        self.p_class = p_class
        self.p_function = p_function
        self.role = role 
        self.offset = offset

    def __str__(self):
        return (f"{str(self.id):<15} {str(self.data_type):<15} {str(self.size):<5}  {str(self.offset):<5} {str(self.scope):<5} "
                f"{str(self.parent_scope):<10} {str(self.p_class):<10} {str(self.p_function):<10} {str(self.role):<10}")

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'p_class': self.p_class,
            'p_function': self.p_function,
            'role': self.role
        })
        return data

class FunctionSymbol(Symbol):
    def __init__(self, id, function_type_obj, scope, parent_scope, parameters=None):
        super().__init__(id, function_type_obj, 0, scope, parent_scope)
        self.parameters = parameters if parameters is not None else []
        self.role = 'Function'

    def __str__(self):
        signature = str(self.data_type)
        return (f"{str(self.id):<15} {signature:<25} {'-':<5} {str(self.scope):<5} {str(self.parent_scope):<10} {'-':<10} {'-':<10} {str(self.role):<10}")

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'role': self.role,
            'parameters': [p.to_dict() for p in self.parameters]
        })
        return data

   
class SymbolTable:
    def __init__(self):
        self.scopes = [{'symbols': {}, 'offset_counter': 0}]  

    def enter_scope(self):
        self.scopes.append({'symbols': {}, 'offset_counter': 0})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add(self, symbol_row):
        current_scope = self.scopes[-1]
        if symbol_row.id in current_scope['symbols']:
            return False

        if isinstance(symbol_row, VariableSymbol):
            if symbol_row.offset is None:
                symbol_row.offset = current_scope['offset_counter']
                current_scope['offset_counter'] += symbol_row.size
            
        current_scope['symbols'][symbol_row.id] = symbol_row
        return True

    def find(self, name):
        for scope in reversed(self.scopes):
            if name in scope['symbols']:
                return scope['symbols'][name]
        return None 

    def get_current_scope_level(self):
        return len(self.scopes)
    
    def find_in_current_scope(self, name):
        current_scope = self.scopes[-1]
        return current_scope['symbols'].get(name)

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

    def to_dict(self):
        table_as_list = []
        for scope in self.scopes:
            scope_symbols = scope['symbols']
            scope_as_dict = {name: symbol.to_dict() for name, symbol in scope_symbols.items()}
            table_as_list.append(scope_as_dict)
        return table_as_list