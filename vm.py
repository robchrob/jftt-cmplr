class Instruction:
    def __init__(self, op, arg=None):
        self.op = op
        self.arg = arg

    def __str__(self):
        if self.arg is not None:
            return f"{self.op} {self.arg}"
        return self.op


class VM:
    """Virtual Machine simulating the register machine architecture"""

    def __init__(self, program, input_data=None, debug=False):
        self.program = program
        self.input_data = input_data or []
        self.input_pos = 0
        self.output = []
        self.debug = debug

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

            if self.debug:
                self._print_debug_info(instr)

            self.execute_instruction(instr)
            if instr.op == "HALT":
                break

        return {
            "output": self.output,
            "steps": self.steps,
            "instructions": self.instructions_executed
        }

    def _print_debug_info(self, instr):
        """Print debug information about current VM state"""
        print(f"\nStep {self.instructions_executed + 1}")
        print(f"Executing: {instr.op} {getattr(instr, 'arg', '')}")
        print(f"Accumulator (A): {self.a}")
        print(f"Instruction counter (K): {self.k}")
        print(f"First 10 memory cells (P): {self.p[:10]}")
        print(f"Output so far: {self.output}")

    def execute_instruction(self, instr):
        """Execute a single instruction"""
        op = instr.op
        self.instructions_executed += 1

        if op == "SCAN":
            i = instr.arg
            if self.input_pos >= len(self.input_data):
                try:
                    value = int(input(f"Enter input value for SCAN instruction {self.instructions_executed}: "))
                    self.input_data.append(value)
                except ValueError:
                    print("Invalid input. Using 0 as default.")
                    value = 0
            else:
                value = self.input_data[self.input_pos]

            self.p[i] = value
            self.input_pos += 1
            self.k += 1
            self.steps += 100

        elif op == "PRINT":
            i = instr.arg
            self.output.append(self.p[i])
            print(f"Output: {self.p[i]}")
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


def parse_program(program_text):
    """Parse program text into list of Instructions"""
    instructions = []
    for line in program_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        op = parts[0]
        arg = int(parts[1]) if len(parts) > 1 else None
        instructions.append(Instruction(op, arg))
    return instructions


# Example usage
if __name__ == "__main__":
    # Example program
    program_text = """
    ZERO
    ZERO
    STORE 0
    ZERO
    INC
    STORE 1
    SCAN 2
    ZERO
    INC
    SHL
    STORE 6
    ZERO
    STORE 0
    LOAD 6
    STORE 1
    LOAD 6
    STORE 2
    LOAD 2
    JZ 32
    LOAD 2
    JODD 22
    JUMP 25
    LOAD 0
    ADD 1
    STORE 0
    LOAD 1
    SHL
    STORE 1
    LOAD 2
    SHR
    STORE 2
    JUMP 17
    LOAD 0
    STORE 3
    PRINT 2
    HALT
    """

    program = parse_program(program_text)
    vm = VM(program, debug=True)
    result = vm.run()
    print("\nFinal result:", result)
