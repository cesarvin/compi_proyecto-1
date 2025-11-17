from recursos.custom_types import *

class TypeRow:
    def __init__(self, data_type, size, inherits= None, attributes = None):
        self.data_type = data_type
        self.size = size 
        self.inherits = inherits
        self.attributes = attributes
        
    def __str__(self):
        return '{0} {1} {2} {3}'.format(self.data_type,self.size, self.inherits, self.attributes)

    def to_dict(self):
        serializable_attrs = None
        if self.attributes:
            serializable_attrs = {name: str(type_obj) for name, type_obj in self.attributes.items()}
        
        return {
            'data_type': str(self.data_type),
            'size': self.size,
            'inherits': self.inherits,
            'attributes': serializable_attrs
        }

class TypeTable:
    def __init__(self):
        self.entries = {
            "object": TypeRow(ObjectType(), 0, None),
            "boolean": TypeRow(BoolType(), 8, "Object"),
            "integer": TypeRow(IntType(), 8, "Object"),
            "float": TypeRow(FloatType(), 8, "Object"),
            "string": TypeRow(StringType(), 8, "Object"),
            "array": TypeRow(ArrayType(ObjectType()), 8, "ArrayObject"),
            "exception": TypeRow(ExceptionType(), 8, "Object"),
            "nil": TypeRow(NilType(), 0, "Object"),
        }
        
        
    def add(self, TypeRow):
        type_name = str(TypeRow.data_type)
        if type_name not in self.entries:
            self.entries[type_name] = TypeRow
            return True
        else:
            return False
    
    def find(self, data_type):
        return self.entries.get(data_type)
    
    def to_dict(self):
        return {name: entry.to_dict() for name, entry in self.entries.items()}

    def print_table(self):
        print("\n" + "=" * 25 + " TYPE TABLE " + "=" * 25)
        
        header = f"{'TYPE NAME':<15} {'SIZE':<10} {'INHERITS':<15} {'ATTRIBUTES'}"
        
        print(header)
        print("-" * 65)

        for type_name, type_row in self.entries.items():
            attributes_str = "N/A"
            if type_row.attributes:
                attributes_str = ", ".join(type_row.attributes.keys())
            
            print(f"{type_name:<15} {str(type_row.size):<10} {str(type_row.inherits):<15} {attributes_str}")
        
        print("=" * 65 + "\n")
