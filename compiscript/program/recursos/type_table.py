from recursos.custom_types import Type, IntType, FloatType, StringType, BoolType, ObjectType, ArrayType

class TypeRow:
    def __init__(self, data_type, size, inherits= None, attributes = None):
        self.data_type = data_type
        self.size = size 
        self.inherits = inherits
        self.attributes = attributes
        
    def __str__(self):
        return '{0} {1} {2} {3}'.format(self.data_type,self.size, self.inherits, self.attributes)

    def to_dict(self):
        return {
            'data_type': self.data_type,
            'size': self.size,
            'inherits': self.inherits,
            'attributes': self.attributes
        }

class TypeTable:
    def __init__(self):
        self.entries = {
            "object": TypeRow(ObjectType(), 0, None),
            "boolean": TypeRow(BoolType(), 1, "Object"),
            "integer": TypeRow(IntType(), 8, "Object"),
            "float": TypeRow(FloatType(), 8, "Object"),
            "string": TypeRow(StringType(), 0, "Object"),
            "array": TypeRow(ArrayType(ObjectType()), 0, "ArrayObject")
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
        #return [entry.to_dict() for entry in self.entries.values()]
        return {name: entry.to_dict() for name, entry in self.entries.items()}