# tests/test_runner.py
import os
import sys
import timeit
import unittest
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler.codegen import CodeGenerator
from vm import VM


class CompilerTestCase(unittest.TestCase):
    """Base class for compiler test cases"""

    def compile_and_run(self, source_code, input_data=None):
        """Compile the source code and run it in the VM"""
        lexer = Lexer()
        tokens = lexer.tokenize(source_code)

        parser = Parser()
        ast = parser.parse(tokens)

        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)

        code_gen = CodeGenerator(symbol_table)
        program = code_gen.generate(ast)

        vm = VM(program, input_data)
        return vm.run()


class BasicTests(CompilerTestCase):
    """Basic functionality tests"""

    def test_arithmetic(self):
        source = """
        CONST zero=0 one=1
        VAR x y z
        BEGIN
          x := 5;
          y := 10;
          z := x + y;
          WRITE z;
          z := y - x;
          WRITE z;
          z := x * y;
          WRITE z;
          z := y / x;
          WRITE z;
          z := y % x;
          WRITE z;
        END
        """
        result = self.compile_and_run(source)
        self.assertEqual(result["output"], [15, 5, 50, 2, 0])

    def test_conditions(self):
        source = """
        CONST zero=0 one=1
        VAR x y z
        BEGIN
          x := 5;
          y := 10;
          IF x < y THEN
            z := 1;
          ELSE
            z := 0;
          END
          WRITE z;

          IF x > y THEN
            z := 1;
          ELSE
            z := 0;
          END
          WRITE z;

          IF x == 5 THEN
            z := 1;
          ELSE
            z := 0;
          END
          WRITE z;
        END
        """
        result = self.compile_and_run(source)
        self.assertEqual(result["output"], [1, 0, 1])

    def test_loops(self):
        source = """
        CONST zero=0 one=1
        VAR i sum
        BEGIN
          i := 1;
          sum := 0;
          WHILE i <= 5 DO
            sum := sum + i;
            i := i + 1;
          END
          WRITE sum;
        END
        """
        result = self.compile_and_run(source)
        self.assertEqual(result["output"], [15])

    def test_io(self):
        source = """
        VAR x y
        BEGIN
          READ x;
          READ y;
          WRITE x;
          WRITE y;
          WRITE x + y;
        END
        """
        input_data = [42, 58]
        result = self.compile_and_run(source, input_data)
        self.assertEqual(result["output"], [42, 58, 100])


class PerformanceTests(CompilerTestCase):
    """Performance tests for arithmetic operations"""

    def test_multiplication_performance(self):
        source = """
        VAR x y z
        BEGIN
          x := 12345;
          y := 67890;
          z := x * y;
          WRITE z;
        END
        """
        result = self.compile_and_run(source)
        # Check logarithmic complexity
        self.assertLess(result["steps"], 100000,
                        "Multiplication should have logarithmic complexity")

    def test_division_performance(self):
        source = """
        VAR x y z
        BEGIN
          x := 1234567;
          y := 89;
          z := x / y;
          WRITE z;
        END
        """
        result = self.compile_and_run(source)
        # Check logarithmic complexity
        self.assertLess(result["steps"], 100000,
                        "Division should have logarithmic complexity")


def run_tests():
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests()
