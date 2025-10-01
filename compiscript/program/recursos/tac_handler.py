class Quadruple:
    def __init__(self, op, arg1, arg2, result):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self):
        if self.op in ['=', 'GOTO', 'PARAM', 'RETURN']:
            return f"{self.result} = {self.op} {self.arg1}"
        elif self.op.startswith('IF'):
            return f"{self.op} {self.arg1} GOTO {self.result}"
        else:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"

class TACode:
    def __init__(self):
        self.instructions = []  # Lista para guardar los objetos Quadruple
        self.temp_counter = 0

    def new_temp(self):
        temp_name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_name

    def add_instruction(self, op, arg1=None, arg2=None, result=None):
        quad = Quadruple(op, arg1, arg2, result)
        self.instructions.append(quad)

    def print_code(self):
        print("\n" + "=" * 20 + " CÓDIGO INTERMEDIO (TAC) " + "=" * 20)
        for i, instruction in enumerate(self.instructions):
            print(f"{i:>3}:  {instruction}")
        print("=" * 66 + "\n")