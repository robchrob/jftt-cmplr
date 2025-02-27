class Instruction:
    def __init__(self, op, arg=None):
        self.op = op
        self.arg = arg

    def __str__(self):
        if self.arg is not None:
            return f"{self.op} {self.arg}"
        return self.op


class CodeGenerator:
    def __init__(self, semantic_analyzer):
        self.analyzer = semantic_analyzer
        self.code = []
        self.memory_map = {}
        self.next_memory = 0
        self.label_counter = 0
        self.labels = {}

        # First allocate constants and variables to memory
        for name in self.analyzer.const_table:
            self.memory_map[name] = self.next_memory
            self.next_memory += 1

        for name in self.analyzer.var_table:
            self.memory_map[name] = self.next_memory
            self.next_memory += 1

    def get_new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def emit(self, op, arg=None):
        self.code.append(Instruction(op, arg))

    def emit_label(self, label):
        self.labels[label] = len(self.code)

    def backpatch(self):
        """Replace label references with actual instruction indices"""
        for i, instr in enumerate(self.code):
            if instr.op in ["JUMP", "JZ", "JG", "JODD"] and isinstance(instr.arg, str):
                if instr.arg in self.labels:
                    self.code[i] = Instruction(instr.op, self.labels[instr.arg])
                else:
                    raise ValueError(f"Undefined label: {instr.arg}")

    def generate(self, ast):
        # Initialize constants
        for name, value in self.analyzer.const_table.items():
            self.emit("ZERO")
            # Generate code to set accumulator to constant value
            self.generate_constant(value)
            # Store the value to memory
            self.emit("STORE", self.memory_map[name])

        # Generate code for commands
        self.generate_commands(ast.commands)

        # End program
        self.emit("HALT")

        # Fix label references
        self.backpatch()

        return self.code, self.memory_map

    def generate_constant(self, value):
        """Generate code to set accumulator to a constant value"""
        # Special case for 0
        if value == 0:
            self.emit("ZERO")
            return

        # Use binary representation for efficient constant generation
        binary = bin(value)[2:]  # Remove '0b' prefix

        self.emit("INC")  # Set a to 1

        for bit in binary[1:]:  # Skip the first bit (already set a to 1)
            self.emit("SHL")    # Double the value
            if bit == '1':
                self.emit("INC")  # Add 1 if bit is set

    def generate_commands(self, commands):
        for command in commands:
            self.generate_command(command)

    def generate_command(self, command):
        from .parser import Assignment, IfElse, While, Read, Write

        if isinstance(command, Assignment):
            self.generate_expression(command.expr)
            self.emit("STORE", self.memory_map[command.name])

        elif isinstance(command, IfElse):
            end_label = self.get_new_label()
            else_label = self.get_new_label()

            # Generate condition code
            self.generate_condition(command.condition, else_label)

            # Generate then part
            self.generate_commands(command.then_cmds)
            self.emit("JUMP", end_label)

            # Generate else part
            self.emit_label(else_label)
            self.generate_commands(command.else_cmds)

            self.emit_label(end_label)

        elif isinstance(command, While):
            start_label = self.get_new_label()
            end_label = self.get_new_label()

            self.emit_label(start_label)

            # Generate condition code
            self.generate_condition(command.condition, end_label)

            # Generate loop body
            self.generate_commands(command.commands)
            self.emit("JUMP", start_label)

            self.emit_label(end_label)

        elif isinstance(command, Read):
            self.emit("SCAN", self.memory_map[command.name])

        elif isinstance(command, Write):
            self.emit("PRINT", self.memory_map[command.name])

    def generate_expression(self, expr):
        from .parser import Number, Identifier, BinOp

        if isinstance(expr, Number):
            self.emit("ZERO")
            self.generate_constant(expr.value)

        elif isinstance(expr, Identifier):
            self.emit("LOAD", self.memory_map[expr.name])

        elif isinstance(expr, BinOp):
            if expr.op == '+':
                self.emit("LOAD", self.memory_map[expr.left.name])
                self.emit("ADD", self.memory_map[expr.right.name])
            elif expr.op == '-':
                self.emit("LOAD", self.memory_map[expr.left.name])
                self.emit("SUB", self.memory_map[expr.right.name])
            elif expr.op == '*':
                self.optimize_multiplication(expr.left.name, expr.right.name)
            elif expr.op == '/':
                self.optimize_division(expr.left.name, expr.right.name)
            elif expr.op == '%':
                self.optimize_modulo(expr.left.name, expr.right.name)

    def optimize_multiplication(self, left, right):
        """Optimize multiplication using binary method (Russian peasant algorithm)"""
        result_addr = 0  # Use p[0] for result
        a_addr = 1       # Use p[1] for a (multiplicand)
        b_addr = 2       # Use p[2] for b (multiplier)

        # Initialize result to 0
        self.emit("ZERO")
        self.emit("STORE", result_addr)

        # Load operands
        self.emit("LOAD", self.memory_map[left])
        self.emit("STORE", a_addr)
        self.emit("LOAD", self.memory_map[right])
        self.emit("STORE", b_addr)

        start_label = self.get_new_label()
        end_label = self.get_new_label()
        odd_label = self.get_new_label()
        after_odd_label = self.get_new_label()

        # Loop start
        self.emit_label(start_label)

        # Check if b is zero
        self.emit("LOAD", b_addr)
        self.emit("JZ", end_label)

        # Check if b is odd
        self.emit("LOAD", b_addr)
        self.emit("JODD", odd_label)
        self.emit("JUMP", after_odd_label)

        # If b is odd, add a to result
        self.emit_label(odd_label)
        self.emit("LOAD", result_addr)
        self.emit("ADD", a_addr)
        self.emit("STORE", result_addr)

        # Double a, halve b
        self.emit_label(after_odd_label)
        self.emit("LOAD", a_addr)
        self.emit("SHL")
        self.emit("STORE", a_addr)
        self.emit("LOAD", b_addr)
        self.emit("SHR")
        self.emit("STORE", b_addr)

        # Jump back to loop start
        self.emit("JUMP", start_label)

        # End of loop
        self.emit_label(end_label)
        self.emit("LOAD", result_addr)

    def optimize_division(self, left, right):
        """Optimize division using binary long division algorithm"""
        quotient_addr = 0    # Use p[0] for quotient
        remainder_addr = 1   # Use p[1] for remainder (dividend)
        divisor_addr = 2     # Use p[2] for divisor

        # Initialize quotient to 0
        self.emit("ZERO")
        self.emit("STORE", quotient_addr)

        # Load operands
        self.emit("LOAD", self.memory_map[left])
        self.emit("STORE", remainder_addr)
        self.emit("LOAD", self.memory_map[right])
        self.emit("STORE", divisor_addr)

        # Check for division by zero
        self.emit("LOAD", divisor_addr)
        zero_div_label = self.get_new_label()
        normal_div_label = self.get_new_label()
        end_label = self.get_new_label()

        self.emit("JZ", zero_div_label)
        self.emit("JUMP", normal_div_label)

        # Handle division by zero: result is 0
        self.emit_label(zero_div_label)
        self.emit("ZERO")
        self.emit("STORE", remainder_addr)
        self.emit("JUMP", end_label)

        # Normal division algorithm
        self.emit_label(normal_div_label)

        # Using long division algorithm
        temp_addr = 3  # Additional temporary storage
        count_addr = 4  # For counting shifts

        # Initialize the temporary variables
        self.emit("ZERO")
        self.emit("STORE", count_addr)

        # First, determine how many times to shift divisor
        shift_start_label = self.get_new_label()
        shift_end_label = self.get_new_label()

        self.emit_label(shift_start_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHL")
        self.emit("STORE", temp_addr)

        # If shifted divisor > remainder, stop shifting
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", temp_addr)
        self.emit("JZ", shift_end_label)

        # Check if we need to stop (if result is < 0)
        comp_label = self.get_new_label()
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", temp_addr)
        self.emit("JG", comp_label)
        self.emit("JUMP", shift_end_label)

        self.emit_label(comp_label)
        self.emit("LOAD", temp_addr)
        self.emit("STORE", divisor_addr)
        self.emit("LOAD", count_addr)
        self.emit("INC")
        self.emit("STORE", count_addr)
        self.emit("JUMP", shift_start_label)

        # Now perform the division
        self.emit_label(shift_end_label)
        div_loop_label = self.get_new_label()
        div_end_label = self.get_new_label()

        self.emit_label(div_loop_label)
        self.emit("LOAD", count_addr)
        self.emit("JZ", div_end_label)

        # Try to subtract
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", divisor_addr)
        sub_possible_label = self.get_new_label()
        no_sub_label = self.get_new_label()

        self.emit("JG", sub_possible_label)
        self.emit("JUMP", no_sub_label)

        # Subtraction is possible, update remainder and quotient
        self.emit_label(sub_possible_label)
        self.emit("STORE", remainder_addr)
        self.emit("LOAD", quotient_addr)
        self.emit("SHL")
        self.emit("INC")
        self.emit("STORE", quotient_addr)
        self.emit("JUMP", shift_divisor_label)

        # Subtraction not possible, just update quotient
        self.emit_label(no_sub_label)
        self.emit("LOAD", quotient_addr)
        self.emit("SHL")
        self.emit("STORE", quotient_addr)

        # Shift divisor right
        shift_divisor_label = self.get_new_label()
        self.emit_label(shift_divisor_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHR")
        self.emit("STORE", divisor_addr)

        # Decrement counter and loop
        self.emit("LOAD", count_addr)
        self.emit("DEC")
        self.emit("STORE", count_addr)
        self.emit("JUMP", div_loop_label)

        # End of division
        self.emit_label(div_end_label)
        self.emit_label(end_label)
        self.emit("LOAD", quotient_addr)

    def optimize_modulo(self, left, right):
        """Optimize modulo operation using the division algorithm"""
        quotient_addr = 0    # Use p[0] for quotient (unused result)
        remainder_addr = 1   # Use p[1] for remainder (result we want)
        divisor_addr = 2     # Use p[2] for divisor

        # Initialize quotient to 0
        self.emit("ZERO")
        self.emit("STORE", quotient_addr)

        # Load operands
        self.emit("LOAD", self.memory_map[left])
        self.emit("STORE", remainder_addr)
        self.emit("LOAD", self.memory_map[right])
        self.emit("STORE", divisor_addr)

        # Check for division by zero
        self.emit("LOAD", divisor_addr)
        zero_div_label = self.get_new_label()
        normal_div_label = self.get_new_label()
        end_label = self.get_new_label()

        self.emit("JZ", zero_div_label)
        self.emit("JUMP", normal_div_label)

        # Handle division by zero: remainder is 0
        self.emit_label(zero_div_label)
        self.emit("ZERO")
        self.emit("STORE", remainder_addr)
        self.emit("JUMP", end_label)

        # Modulo algorithm (similar to division but we keep the remainder)
        self.emit_label(normal_div_label)

        # Using the same division algorithm but we'll return the remainder
        temp_addr = 3
        count_addr = 4

        # Initialize the temporary variables
        self.emit("ZERO")
        self.emit("STORE", count_addr)

        # First, determine how many times to shift divisor
        shift_start_label = self.get_new_label()
        shift_end_label = self.get_new_label()

        self.emit_label(shift_start_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHL")
        self.emit("STORE", temp_addr)

        # If shifted divisor > remainder, stop shifting
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", temp_addr)
        self.emit("JZ", shift_end_label)

        # Check if we need to stop (if result is < 0)
        comp_label = self.get_new_label()
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", temp_addr)
        self.emit("JG", comp_label)
        self.emit("JUMP", shift_end_label)

        self.emit_label(comp_label)
        self.emit("LOAD", temp_addr)
        self.emit("STORE", divisor_addr)
        self.emit("LOAD", count_addr)
        self.emit("INC")
        self.emit("STORE", count_addr)
        self.emit("JUMP", shift_start_label)

        # Now perform the division
        self.emit_label(shift_end_label)
        div_loop_label = self.get_new_label()
        div_end_label = self.get_new_label()

        self.emit_label(div_loop_label)
        self.emit("LOAD", count_addr)
        self.emit("JZ", div_end_label)

        # Try to subtract
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", divisor_addr)
        sub_possible_label = self.get_new_label()
        no_sub_label = self.get_new_label()

        self.emit("JG", sub_possible_label)
        self.emit("JUMP", no_sub_label)

        # Subtraction is possible, update remainder
        self.emit_label(sub_possible_label)
        self.emit("STORE", remainder_addr)
        # We don't care about the quotient for modulo

        # Shift divisor right regardless
        self.emit_label(no_sub_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHR")
        self.emit("STORE", divisor_addr)

        # Decrement counter and loop
        self.emit("LOAD", count_addr)
        self.emit("DEC")
        self.emit("STORE", count_addr)
        self.emit("JUMP", div_loop_label)

        # End of modulo operation
        self.emit_label(div_end_label)
        self.emit_label(end_label)
        # Load the remainder instead of quotient
        self.emit("LOAD", remainder_addr)

    def generate_condition(self, condition, false_label):
        """Generate code for conditional expressions"""
        left_name = condition.left.name
        right_name = condition.right.name

        # Load first operand to accumulator
        self.emit("LOAD", self.memory_map[left_name])

        if condition.op == '==':
            # a == b: Subtract b from a, jump if not zero
            self.emit("SUB", self.memory_map[right_name])
            self.emit("JZ", false_label)

        elif condition.op == '!=':
            # a != b: Subtract b from a, jump if zero
            self.emit("SUB", self.memory_map[right_name])
            temp = self.get_new_label()
            self.emit("JZ", temp)
            self.emit("JUMP", false_label)
            self.emit_label(temp)

        elif condition.op == '<':
            # a < b: Subtract b from a, then add 1, jump if greater or equal
            self.emit("SUB", self.memory_map[right_name])
            self.emit("INC")  # To handle a - b < 0 as a - b + 1 <= 0
            self.emit("JG", false_label)

        elif condition.op == '>':
            # a > b: Subtract b from a, jump if less than or equal
            self.emit("SUB", self.memory_map[right_name])
            self.emit("JZ", false_label)  # If a - b = 0 then a = b, so not a > b
            self.emit("JG", false_label)  # If a - b > 0 then a < b, so not a > b

        elif condition.op == '<=':
            # a <= b: Subtract b from a, jump if greater
            self.emit("SUB", self.memory_map[right_name])
            self.emit("JG", false_label)

        elif condition.op == '>=':
            # a >= b: Subtract b from a, jump if less than
            self.emit("SUB", self.memory_map[right_name])
            temp = self.get_new_label()
            self.emit("JZ", temp)
            self.emit("JG", false_label)
            self.emit_label(temp)
