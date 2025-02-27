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

        # First allocate constants to memory
        for name in self.analyzer.const_table:
            self.memory_map[name] = self.next_memory
            self.next_memory += 1

        # Allocate user variables to memory
        for name in self.analyzer.var_table:
            self.memory_map[name] = self.next_memory
            self.next_memory += 1

        # Reserve 5 temporary memory locations after user variables
        self.temp_start = self.next_memory
        self.next_memory += 5  # Adjust based on maximum temps needed

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

        self.emit("INC")  # Set accumulator to 1

        for bit in binary[1:]:  # Skip the first bit (already set to 1)
            self.emit("SHL")  # Double the value
            if bit == '1':
                self.emit("INC")  # Add 1 if bit is set

    def generate_commands(self, commands):
        for command in commands:
            self.generate_command(command)

    def generate_command(self, command):
        from .parser import Assignment, IfElse, While, Read, Write

        if isinstance(command, Assignment):
            self.generate_expression(command.expr)
            # Store result to the correctly allocated user variable address
            self.emit("STORE", self.memory_map[command.name])

        elif isinstance(command, IfElse):
            end_label = self.get_new_label()
            else_label = self.get_new_label()

            # Generate condition code, jumping to else label if condition fails
            self.generate_condition(command.condition, else_label)

            # Generate then part commands
            self.generate_commands(command.then_cmds)
            self.emit("JUMP", end_label)

            # Generate else part commands
            self.emit_label(else_label)
            self.generate_commands(command.else_cmds)

            self.emit_label(end_label)

        elif isinstance(command, While):
            start_label = self.get_new_label()
            end_label = self.get_new_label()

            self.emit_label(start_label)

            # Generate the condition, jumping to end label if false
            self.generate_condition(command.condition, end_label)

            # Generate loop body
            self.generate_commands(command.commands)
            self.emit("JUMP", start_label)

            self.emit_label(end_label)

        elif isinstance(command, Read):
            # Read input into the variable's allocated address
            self.emit("SCAN", self.memory_map[command.name])

        elif isinstance(command, Write):
            # Write output from the variable's allocated address
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
                # For simplicity, use LOAD and ADD for addition
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
        """Optimize multiplication using binary method (Russian peasant algorithm)
        with reserved temporary memory.
        """
        # Use reserved temporary addresses
        result_addr = self.temp_start       # Result storage
        a_addr = self.temp_start + 1        # Multiplicand
        b_addr = self.temp_start + 2        # Multiplier

        # Initialize result to 0
        self.emit("ZERO")
        self.emit("STORE", result_addr)

        # Load operands from their memory locations
        self.emit("LOAD", self.memory_map[left])
        self.emit("STORE", a_addr)
        self.emit("LOAD", self.memory_map[right])
        self.emit("STORE", b_addr)

        start_label = self.get_new_label()
        end_label = self.get_new_label()
        odd_label = self.get_new_label()
        after_odd_label = self.get_new_label()

        # Start loop for multiplication
        self.emit_label(start_label)

        # Check if b is zero; if yes, end loop
        self.emit("LOAD", b_addr)
        self.emit("JZ", end_label)

        # Check if b is odd; if so jump to odd_label
        self.emit("LOAD", b_addr)
        self.emit("JODD", odd_label)
        self.emit("JUMP", after_odd_label)

        # If b is odd, add a to result
        self.emit_label(odd_label)
        self.emit("LOAD", result_addr)
        self.emit("ADD", a_addr)
        self.emit("STORE", result_addr)

        # Continue with doubling a and halving b
        self.emit_label(after_odd_label)
        self.emit("LOAD", a_addr)
        self.emit("SHL")
        self.emit("STORE", a_addr)
        self.emit("LOAD", b_addr)
        self.emit("SHR")
        self.emit("STORE", b_addr)

        # Jump back to loop start
        self.emit("JUMP", start_label)

        # End loop and load the multiplication result
        self.emit_label(end_label)
        self.emit("LOAD", result_addr)

    def optimize_division(self, left, right):
        """Optimize division using binary long division algorithm with
        reserved temporary memory.
        """
        # Reserved addresses:
        quotient_addr = self.temp_start       # quotient
        remainder_addr = self.temp_start + 1    # remainder (dividend)
        divisor_addr = self.temp_start + 2      # divisor
        temp_addr = self.temp_start + 3         # temporary storage
        count_addr = self.temp_start + 4        # shift counter

        # Initialize quotient to 0
        self.emit("ZERO")
        self.emit("STORE", quotient_addr)

        # Load dividend and divisor operands
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

        # Handle division by zero: return 0 in remainder
        self.emit_label(zero_div_label)
        self.emit("ZERO")
        self.emit("STORE", remainder_addr)
        self.emit("JUMP", end_label)

        # Proceed with normal division
        self.emit_label(normal_div_label)

        # Initialize temporary count to 0
        self.emit("ZERO")
        self.emit("STORE", count_addr)

        # Determine the number of left shifts needed for the divisor
        shift_start_label = self.get_new_label()
        shift_end_label = self.get_new_label()

        self.emit_label(shift_start_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHL")
        self.emit("STORE", temp_addr)

        # If shifted divisor is exactly equal to remainder: stop shifting
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", temp_addr)
        self.emit("JZ", shift_end_label)

        # Check if subtraction result is positive (greater than 0)
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

        # Division loop: perform subtraction and shift operations
        self.emit_label(shift_end_label)
        div_loop_label = self.get_new_label()
        div_end_label = self.get_new_label()

        self.emit_label(div_loop_label)
        self.emit("LOAD", count_addr)
        self.emit("JZ", div_end_label)

        # Attempt subtraction: remainder - divisor
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", divisor_addr)
        sub_possible_label = self.get_new_label()
        no_sub_label = self.get_new_label()

        self.emit("JG", sub_possible_label)
        self.emit("JUMP", no_sub_label)

        # If subtraction is possible, update remainder and quotient (append 1)
        self.emit_label(sub_possible_label)
        self.emit("STORE", remainder_addr)
        self.emit("LOAD", quotient_addr)
        self.emit("SHL")
        self.emit("INC")
        self.emit("STORE", quotient_addr)
        self.emit("JUMP", "shift_divisor_div")  # Jump to divisor shifting

        # If subtraction is not possible, just update quotient (append 0)
        self.emit_label(no_sub_label)
        self.emit("LOAD", quotient_addr)
        self.emit("SHL")
        self.emit("STORE", quotient_addr)

        # Label for shifting the divisor right
        shift_divisor_label = self.get_new_label()
        self.emit_label(shift_divisor_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHR")
        self.emit("STORE", divisor_addr)

        # Decrement counter and loop back
        self.emit("LOAD", count_addr)
        self.emit("DEC")
        self.emit("STORE", count_addr)
        self.emit("JUMP", div_loop_label)

        self.emit_label(div_end_label)
        self.emit_label(end_label)
        # Load the quotient as the result for division
        self.emit("LOAD", quotient_addr)

    def optimize_modulo(self, left, right):
        """Optimize modulo operation using the division algorithm and
        reserved temporary memory.
        """
        # Reserved addresses (same as for division)
        quotient_addr = self.temp_start       # quotient (unused for modulo)
        remainder_addr = self.temp_start + 1    # remainder (result needed)
        divisor_addr = self.temp_start + 2      # divisor
        temp_addr = self.temp_start + 3         # temporary storage
        count_addr = self.temp_start + 4        # shift counter

        # Initialize quotient to 0 (though for modulo we only care about remainder)
        self.emit("ZERO")
        self.emit("STORE", quotient_addr)

        # Load operands for the modulo operation
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

        # For division-by-zero, modulo is defined as 0
        self.emit_label(zero_div_label)
        self.emit("ZERO")
        self.emit("STORE", remainder_addr)
        self.emit("JUMP", end_label)

        # Proceed with normal modulo calculation (similar to division)
        self.emit_label(normal_div_label)

        # Initialize shift counter to 0
        self.emit("ZERO")
        self.emit("STORE", count_addr)

        # Determine number of left shifts for the divisor
        shift_start_label = self.get_new_label()
        shift_end_label = self.get_new_label()

        self.emit_label(shift_start_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHL")
        self.emit("STORE", temp_addr)

        self.emit("LOAD", remainder_addr)
        self.emit("SUB", temp_addr)
        self.emit("JZ", shift_end_label)

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

        # Modulo division loop
        self.emit_label(shift_end_label)
        div_loop_label = self.get_new_label()
        div_end_label = self.get_new_label()

        self.emit_label(div_loop_label)
        self.emit("LOAD", count_addr)
        self.emit("JZ", div_end_label)

        # Try to subtract divisor from remainder
        self.emit("LOAD", remainder_addr)
        self.emit("SUB", divisor_addr)
        sub_possible_label = self.get_new_label()
        no_sub_label = self.get_new_label()

        self.emit("JG", sub_possible_label)
        self.emit("JUMP", no_sub_label)

        # If subtraction is possible, update remainder
        self.emit_label(sub_possible_label)
        self.emit("STORE", remainder_addr)
        # We do not update quotient for modulo

        # In all cases, shift the divisor right
        self.emit_label(no_sub_label)
        self.emit("LOAD", divisor_addr)
        self.emit("SHR")
        self.emit("STORE", divisor_addr)

        # Decrement the shift counter and repeat
        self.emit("LOAD", count_addr)
        self.emit("DEC")
        self.emit("STORE", count_addr)
        self.emit("JUMP", div_loop_label)

        self.emit_label(div_end_label)
        self.emit_label(end_label)
        # For modulo, the remainder is the final result
        self.emit("LOAD", remainder_addr)

    def generate_condition(self, condition, false_label):
        """Generate code for conditional expressions.

        This implementation subtracts the second operand from the first
        and then uses conditional jumps.
        """
        left_name = condition.left.name
        right_name = condition.right.name

        # Load the left operand into the accumulator
        self.emit("LOAD", self.memory_map[left_name])

        if condition.op == '==':
            # For a == b, subtract b; if zero then condition is true.
            self.emit("SUB", self.memory_map[right_name])
            self.emit("JZ", false_label)

        elif condition.op == '!=':
            # a != b: subtract b; if zero, then jump to a temporary label
            self.emit("SUB", self.memory_map[right_name])
            temp = self.get_new_label()
            self.emit("JZ", temp)
            self.emit("JUMP", false_label)
            self.emit_label(temp)

        elif condition.op == '<':
            # For a < b, subtract b then adjust before comparing
            self.emit("SUB", self.memory_map[right_name])
            self.emit("INC")  # Adjust, so that a - b < 0 becomes <= 0
            self.emit("JG", false_label)

        elif condition.op == '>':
            # For a > b, subtract b and jump if equal or greater (not >)
            self.emit("SUB", self.memory_map[right_name])
            self.emit("JZ", false_label)
            self.emit("JG", false_label)

        elif condition.op == '<=':
            # For a <= b, subtract b and jump if result is positive (i.e., > 0)
            self.emit("SUB", self.memory_map[right_name])
            self.emit("JG", false_label)

        elif condition.op == '>=':
            # For a >= b, subtract b and jump if result is negative
            self.emit("SUB", self.memory_map[right_name])
            temp = self.get_new_label()
            self.emit("JZ", temp)
            self.emit("JG", false_label)
            self.emit_label(temp)
