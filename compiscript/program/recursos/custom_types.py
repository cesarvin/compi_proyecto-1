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
    return "integer"

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
    return "boolean"

class ArrayType(Type):
    def __init__(self, element_type):
        self.element_type = element_type

    def __eq__(self, other):
        if not isinstance(other, ArrayType):
            return False
        return self.element_type == other.element_type

    def __str__(self):
        return f"Array<{self.element_type}>"  
    
class ErrorType(Type):
    def __eq__(self, other):
        return isinstance(other, ErrorType)

    def __str__(self):
        return "error"

class ExceptionType(Type):
  def __eq__(self, other):
    return isinstance(other, ExceptionType)
  
  def __str__(self):
    return "exception"

class NilType(Type):
  def __eq__(self, other):
    return isinstance(other, NilType)
  
  def __str__(self):
    return "nil"

class FunctionType(Type):
    def __init__(self, return_type, param_types):
        self.return_type = return_type
        self.param_types = param_types

    def __eq__(self, other):
        if not isinstance(other, FunctionType):
            return False
        return self.return_type == other.return_type and self.param_types == other.param_types

    def __str__(self):
        params = ", ".join(str(p) for p in self.param_types)
        return f"({params}) -> {self.return_type}"

class ClassType(Type):
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, ClassType) and self.name == other.name
  
    def __str__(self):
        return str(self.name)