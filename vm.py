# vm.py
class VM:
    """Virtual Machine simulating the register machine architecture"""

    def __init__(self, program, input_data=None):
        self.program = program
        self.input_data = input_data or []
        self.input_pos = 0
        self.output = []

        # Machine state
        self.a = 0  # Accumulator register
        self.k = 0  # Instruction counter
        self.p = [0] * 1000  # Memory (we'll use 1000 cells)

        # Statistics
        self.steps = 0
        self.instructions_executed = 0

    def run(self):
        """Execute the program until HALT instruction"""
        while self.k < len(self.program):
            instr = self.program[self.k]
            self.execute_instruction(instr)
            if instr.op == "HALT":
                break

        return {
            "output": self.output,
            "steps": self.steps,
            "instructions": self.instructions_executed
        }

    def execute_instruction(self, instr):
        """Execute a single instruction"""
        op = instr.op
        self.instructions_executed += 1

        if op == "SCAN":
            i = instr.arg
            if self.input_pos < len(self.input_data):
                self.p[i] = self.input_data[self.input_pos]
                self.input_pos += 1
            else:
                self.p[i] = 0  # Default if no more input
            self.k += 1
            self.steps += 100

        elif op == "PRINT":
            i = instr.arg
            self.output.append(self.p[i])
            self.k += 1
            self.steps += 100

        elif op == "LOAD":
            i = instr.arg
            self.a = self.p[i]
            self.k += 1
            self.steps += 10 if i < 3 else 100

        elif op == "STORE":
            i = instr.arg
            self.p[i] = self.a
            self.k += 1
            self.steps += 10 if i < 3 else 100

        elif op == "ADD":
            i = instr.arg
            self.a += self.p[i]
            self.k += 1
            self.steps += 10 if i < 3 else 100

        elif op == "SUB":
            i = instr.arg
            self.a = max(self.a - self.p[i], 0)
            self.k += 1
            self.steps += 10 if i < 3 else 100

        elif op == "SHR":
            self.a = self.a // 2
            self.k += 1
            self.steps += 1

        elif op == "SHL":
            self.a = 2 * self.a
            self.k += 1
            self.steps += 1

        elif op == "INC":
            self.a += 1
            self.k += 1
            self.steps += 1

        elif op == "DEC":
            self.a = max(self.a - 1, 0)
            self.k += 1
            self.steps += 1

        elif op == "ZERO":
            self.a = 0
            self.k += 1
            self.steps += 1

        elif op == "JUMP":
            i = instr.arg
            self.k = i
            self.steps += 1

        elif op == "JZ":
            i = instr.arg
            if self.a == 0:
                self.k = i
            else:
                self.k += 1
            self.steps += 1

        elif op == "JG":
            i = instr.arg
            if self.a > 0:
                self.k = i
            else:
                self.k += 1
            self.steps += 1

        elif op == "JODD":
            i = instr.arg
            if self.a % 2 == 1:
                self.k = i
            else:
                self.k += 1
            self.steps += 1

        elif op == "HALT":
            self.steps += 0  # HALT costs 0 steps

        else:
            raise ValueError(f"Unknown instruction: {op}")
