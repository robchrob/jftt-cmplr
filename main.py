import sys
import argparse
from compiler.lexer import lexer
from compiler.parser import parse
from compiler.semantic import SemanticAnalyzer
from compiler.codegen import CodeGenerator
from vm import VM


def main():
    parser = argparse.ArgumentParser(description='Compiler for a simple imperative language')
    parser.add_argument('file', help='Source file to compile')
    parser.add_argument('--output', '-o', help='Output file for generated code', default=None)
    parser.add_argument('--run', '-r', action='store_true', help='Run the program after compilation')
    parser.add_argument('--input', '-i', help='Input file for program execution', default=None)
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose mode')

    args = parser.parse_args()

    try:
        with open(args.file, 'r') as f:
            source_code = f.read()

        # Parse the source code using the lexer and parser
        ast = parse(source_code, lexer=lexer)

        # Semantic analysis
        analyzer = SemanticAnalyzer()
        is_valid, errors = analyzer.analyze(ast)
        if not is_valid:
            raise Exception(f"Semantic errors: {errors}")

        # Code generation
        code_gen = CodeGenerator(analyzer)
        program, _ = code_gen.generate(ast)

        # Output generated code
        if args.output:
            with open(args.output, 'w') as f:
                for instr in program:
                    f.write(f"{instr.op} {instr.arg if instr.arg is not None else ''}\n")

        if args.verbose:
            print(f"Compilation successful. Generated {len(program)} instructions.")

        # Run the program
        if args.run:
            input_data = []
            if args.input:
                with open(args.input, 'r') as f:
                    input_data = [int(line.strip()) for line in f]

            vm = VM(program, input_data)
            result = vm.run()

            print("Program output:")
            for value in result["output"]:
                print(value)

            if args.verbose:
                print(f"\nExecution statistics:")
                print(f"Instructions executed: {result['instructions']}")
                print(f"Steps executed: {result['steps']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
