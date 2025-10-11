class Quadruple:
    def __init__(self, op, arg1, arg2, result):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self):
        if self.op.endswith(':'):
            return f"  {self.op}"

        elif self.op in ['CALL', 'NEW', 'ALLOCATE']:
            result_str = f"{self.result} = " if self.result else ""
            arg2_str = f", {self.arg2}" if self.arg2 is not None else ""
            return f"  {result_str}{self.op} {self.arg1}{arg2_str}"

        elif self.op == '=':
            return f"  {self.result} = {self.arg1}"

        elif self.op.startswith('IF'):
            return f"  {self.op} {self.arg1} GOTO {self.result}"
        elif self.op == 'GOTO':
            return f"  {self.op} {self.result}"
        
        elif self.op in ['PARAM', 'RETURN', 'BEGIN_FUNC', 'END_FUNC', 'TRY_BEGIN', 'TRY_END']:
            arg1_str = f" {self.arg1}" if self.arg1 is not None else ""
            return f"  {self.op}{arg1_str}"

        else:
            return f"  {self.result} = {self.arg1} {self.op} {self.arg2}"

class TACode:
    def __init__(self):
        self.instructions = []
        self.temp_counter = 0

    def add_temp(self):
        temp_name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_name

    def add_quadruple(self, op, arg1=None, arg2=None, result=None):
        quad = Quadruple(op, arg1, arg2, result)
        self.instructions.append(quad)

    def print_code(self):
        print("\n" + "=" * 20 + " CÓDIGO INTERMEDIO (TAC) " + "=" * 20)
        for i, instruction in enumerate(self.instructions):
            print(f"{i:>3}:  {instruction}")
        print("=" * 66 + "\n")