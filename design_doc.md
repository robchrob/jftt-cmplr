1. Introduction

This project implements a compiler for a simple imperative language, translating source code into optimized register machine code. The system is built in Python using PLY (Python Lex-Yacc) for parsing and adheres strictly to the blueprint's specifications. The design includes:

    A Compiler with lexical analysis, parsing, semantic checks, and code generation.

    A Virtual Machine (VM) simulating the register machine architecture.

    An Advanced Testing Framework for performance profiling and correctness verification.

2. Project Objectives & Requirements

    Language Conformance: Accept programs adhering to the specified grammar.

    Error Handling: Report errors (e.g., duplicate declarations, undeclared variables) with line/column positions.

    Optimized Code Generation: Ensure arithmetic operations (especially * and /) compile to code with logarithmic time complexity relative to operand size.

    Modularity: Clear separation between compiler, VM, and testing modules.

    Build & Documentation: Include a Makefile and README for building, testing, and usage.

3. Language Specification
3.1 Grammar
ebnf
Copy

program -> CONST cdeclarations VAR vdeclarations BEGIN commands END
cdeclarations -> cdeclarations identifier=num | ε
vdeclarations -> vdeclarations identifier | ε
commands -> commands command | command
command -> identifier := expression; 
           | IF condition THEN commands ELSE commands END 
           | WHILE condition DO commands END 
           | READ identifier; 
           | WRITE identifier;
expression -> num | identifier 
             | identifier + identifier 
             | identifier - identifier 
             | identifier * identifier 
             | identifier / identifier 
             | identifier % identifier
condition -> identifier == identifier 
            | identifier != identifier 
            | identifier < identifier 
            | identifier > identifier 
            | identifier <= identifier 
            | identifier >= identifier

3.2 Lexical Rules

    Identifier: [_a-z]+ (case-sensitive, e.g., var1 ≠ Var1).

    Number: Natural numbers in decimal (unbounded size).

    Comments: Enclosed in (* ... *) (non-nestable).

3.3 Semantic Rules

    Declarations: Constants/variables must be declared before use. Duplicates are errors.

    Arithmetic:

        Subtraction: a - b = max(a - b, 0).

        Division by zero: Yields quotient 0 and remainder 0.

    I/O: READ writes to a variable; WRITE outputs a variable/number.

4. Register Machine Specification
4.1 Architecture

    Register a: Holds temporary results.

    Instruction Counter k: Starts at 0.

    Memory p[i]: Cells p[0], p[1], p[2] have faster access times.

4.2 Instruction Set & Timing
Instruction	Interpretation	Execution Time (Steps)
SCAN i	Read into p[i], k++	100
PRINT i	Output p[i], k++	100
LOAD i	a = p[i], k++	10 if i < 3, else 100
STORE i	p[i] = a, k++	10 if i < 3, else 100
ADD i	a += p[i], k++	10 if i < 3, else 100
SUB i	a = max(a - p[i], 0), k++	10 if i < 3, else 100
SHR	a = a // 2, k++	1
SHL	a = 2 * a, k++	1
INC/DEC	a++/a-- (min 0), k++	1
ZERO	a = 0, k++	1
JUMP i	k = i	1
JZ i/JG i/JODD i	Conditional jump, k++ if false	1
HALT	Stop execution	0
5. System Architecture
5.1 Compiler Module

    Lexical Analyzer (lex.py): Tokenizes input using regex. Reports lexical errors.

    Parser (parser.py): Uses PLY to build an AST from the grammar.

    Semantic Analyzer (semantic.py): Manages symbol tables and enforces rules (e.g., no undeclared variables).

    Code Generator (codegen.py): Translates AST to optimized machine code:

        Optimizations:

            Multiplication/Division: Use bit-shifting (SHL/SHR) and additive operations for logarithmic time.

            Division by Zero: Insert checks to set result to 0 if divisor is zero.

            Fast Memory Access: Prioritize p[0-2] for frequently used variables.

5.2 Virtual Machine (vm.py)

    Execution Loop: Fetches, decodes, and executes instructions.

    Memory Management: Simulates fast (p[0-2]) vs. slow memory access times.

    Error Handling: Detects invalid jumps and halts with errors.

5.3 Advanced Testing Framework

    Benchmarks: Measure instruction count, execution steps, and compiler runtime.

    Correctness Tests: Validate VM output against expected results.

    Performance Profiling: Ensure arithmetic operations (e.g., n = 1234567890) execute in ~O(log n) steps.

6. Implementation Details
6.1 Code Generation for Arithmetic

    Multiplication:

        For x * y, generate code using repeated addition and shifts (e.g., decompose y into binary components).

        Example: x * 2 → SHL once.

    Division/Modulo:

        Use SHR for powers of two. For variable divisors, implement long division via subtraction and shifts.

6.2 Example: Optimized Division
python
Copy

# Code snippet from codegen.py for a / b:
if b == 0:
    emit ZERO  # Handle division by zero
else:
    emit LOAD b
    emit LOAD a
    emit SUB b  # Repeated subtraction loop with shifts
    ...

7. Build & Execution
7.1 File Structure
Copy

/project_root
├── Makefile       # Build, test, and clean
├── README.md      # Usage, examples, testing
├── main.py        # CLI entry point
├── compiler/      # Lexer, parser, codegen
├── vm/            # Virtual machine
└── tests/         # Test cases and benchmarks

7.2 Makefile Targets
makefile
Copy

build:   # Compile the compiler
test:    # Run all tests
profile: # Benchmark performance
clean:   # Remove generated files

8. Example & Validation
8.1 Sample Program (Factorize)
plaintext
Copy

CONST zero=0 jeden=1
VAR n m reszta potega dzielnik
BEGIN
  READ n;
  dzielnik := 2;
  m := dzielnik * dzielnik;
  WHILE n >= m DO
    potega := 0;
    reszta := n % dzielnik;
    WHILE reszta == zero DO
      n := n / dzielnik;
      potega := potega + jeden;
      reszta := n % dzielnik;
    END;
    IF potega > zero THEN
      WRITE dzielnik;
      WRITE potega;
    ELSE
      dzielnik := dzielnik + jeden;
      m := dzielnik * dzielnik;
    END;
  END;
  IF n != jeden THEN
    WRITE n;
    WRITE jeden;
  END;
END

8.2 Expected Output
plaintext
Copy

> 1234567890
2 1 3 2 5 1 3607 1 3803 1
Steps executed: ~4,000,000 (logarithmic scaling)

