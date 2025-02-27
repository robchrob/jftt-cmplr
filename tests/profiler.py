# tests/profiler.py
import time
import matplotlib.pyplot as plt
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler.codegen import CodeGenerator
from vm import VM


def profile_arithmetic_operation(operation, values, title):
    """Profile an arithmetic operation with different operand sizes"""
    steps_list = []
    sizes = []

    for n in values:
        source = f"""
        VAR x y z
        BEGIN
          x := {n};
          y := 42;
          z := x {operation} y;
          WRITE z;
        END
        """

        # Compile
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        parser = Parser()
        ast = parser.parse(tokens)

        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)

        code_gen = CodeGenerator(symbol_table)
        program = code_gen.generate(ast)

        # Run
        vm = VM(program)
        result = vm.run()

        steps_list.append(result["steps"])
        sizes.append(n)

        print(f"Operation: {n} {operation} 42, Steps: {result['steps']}")

    # Plot results
    plt.figure(figsize=(10, 6))
    plt.plot(sizes, steps_list, marker='o')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Operand Size')
    plt.ylabel('Execution Steps')
    plt.title(f'Performance of {operation.upper()} Operation')
    plt.grid(True)
    plt.savefig(f'profile_{operation.replace("/", "div")}.png')
    plt.close()


def run_profiling():
    """Run performance profiling for all arithmetic operations"""
    values = [10, 100, 1000, 10000, 100000, 1000000, 10000000]

    print("Profiling addition...")
    profile_arithmetic_operation("+", values, "Addition")

    print("Profiling subtraction...")
    profile_arithmetic_operation("-", values, "Subtraction")

    print("Profiling multiplication...")
    profile_arithmetic_operation("*", values, "Multiplication")

    print("Profiling division...")
    profile_arithmetic_operation("/", values, "Division")

    print("Profiling modulo...")
    profile_arithmetic_operation("%", values, "Modulo")

    print("Profiling complete. Check the generated PNG files for visualization.")


if __name__ == "__main__":
    run_profiling()
