class Type:
  pass

class ObjectType(Type):
  def __eq__(self, other):
    return isinstance(other, ObjectType)
  
  def __str__(self):
    return "object"

class IntType(Type):
  def __eq__(self, other):
    return isinstance(other, IntType)
  
  def __str__(self):
    return "int"

class FloatType(Type):
  def __eq__(self, other):
        return isinstance(other, FloatType)

  def __str__(self):
    return "float"

class StringType(Type):
  def __eq__(self, other):
      return isinstance(other, StringType)

  def __str__(self):
    return "string"

class BoolType(Type):
  def __eq__(self, other):
      return isinstance(other, BoolType)

  def __str__(self):
    return "bool"

class ArrayType(Type):
    def __init__(self, element_type):
        self.element_type = element_type

    def __eq__(self, other):
        if not isinstance(other, ArrayType):
            return False
        return self.element_type == other.element_type

    def __str__(self):
        return f"Array<{self.element_type}>"  