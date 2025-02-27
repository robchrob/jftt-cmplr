from .parser import *


class SemanticAnalyzer:
    def __init__(self):
        self.const_table = {}  # name -> value
        self.var_table = {}    # name -> address
        self.next_address = 0  # Memory allocation counter
        self.errors = []

    def analyze(self, ast):
        # Process constant declarations
        for const_decl in ast.const_decls:
            if const_decl.name in self.const_table or const_decl.name in self.var_table:
                self.errors.append(f"Duplicate declaration of identifier '{const_decl.name}'")
            else:
                self.const_table[const_decl.name] = const_decl.value

        # Process variable declarations
        for var_decl in ast.var_decls:
            if var_decl.name in self.const_table or var_decl.name in self.var_table:
                self.errors.append(f"Duplicate declaration of identifier '{var_decl.name}'")
            else:
                self.var_table[var_decl.name] = self.next_address
                self.next_address += 1

        # Check commands recursively
        self._check_commands(ast.commands)

        return len(self.errors) == 0, self.errors

    def _check_commands(self, commands):
        for cmd in commands:
            self._check_command(cmd)

    def _check_command(self, cmd):
        if isinstance(cmd, Assignment):
            # Check if the target variable exists
            if cmd.name not in self.var_table:
                self.errors.append(f"Assignment to undeclared variable '{cmd.name}'")
            # Check the expression
            self._check_expression(cmd.expr)

        elif isinstance(cmd, IfElse):
            self._check_condition(cmd.condition)
            self._check_commands(cmd.then_cmds)
            self._check_commands(cmd.else_cmds)

        elif isinstance(cmd, While):
            self._check_condition(cmd.condition)
            self._check_commands(cmd.commands)

        elif isinstance(cmd, Read):
            if cmd.name not in self.var_table:
                self.errors.append(f"READ into undeclared variable '{cmd.name}'")

        elif isinstance(cmd, Write):
            if cmd.name not in self.var_table and cmd.name not in self.const_table:
                self.errors.append(f"WRITE undeclared identifier '{cmd.name}'")

    def _check_expression(self, expr):
        if isinstance(expr, Number):
            # Numbers are always valid
            pass

        elif isinstance(expr, Identifier):
            # Check if the identifier exists
            if expr.name not in self.var_table and expr.name not in self.const_table:
                self.errors.append(f"Reference to undeclared identifier '{expr.name}'")

        elif isinstance(expr, BinOp):
            # Check both operands
            if isinstance(expr.left, Identifier):
                if expr.left.name not in self.var_table and expr.left.name not in self.const_table:
                    self.errors.append(f"Reference to undeclared identifier '{expr.left.name}'")

            if isinstance(expr.right, Identifier):
                if expr.right.name not in self.var_table and expr.right.name not in self.const_table:
                    self.errors.append(f"Reference to undeclared identifier '{expr.right.name}'")

    def _check_condition(self, condition):
        # Check both sides of the condition
        if condition.left.name not in self.var_table and condition.left.name not in self.const_table:
            self.errors.append(f"Reference to undeclared identifier '{condition.left.name}'")

        if condition.right.name not in self.var_table and condition.right.name not in self.const_table:
            self.errors.append(f"Reference to undeclared identifier '{condition.right.name}'")
