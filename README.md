# Simple Imperative Language Compiler

A compiler for a simple imperative language that translates source code into optimized register machine code.

## Features

- **Full Compiler Pipeline**: Lexical analysis, parsing, semantic checks, and code generation
- **Virtual Machine**: Simulates the register machine architecture
- **Optimized Code Generation**: Logarithmic time complexity for arithmetic operations
- **Error Handling**: Reports syntax and semantic errors with line/column positions

## Building and Running

### Prerequisites

- Python 3.6 or higher
- PLY (Python Lex-Yacc) library: `pip install ply`
- Matplotlib (for profiling): `pip install matplotlib`

### Installation

```bash
git clone https://github.com/yourusername/simple-compiler.git
cd simple-compiler


### Usage
Compile and run on VM
python main.py program.gbl -o out.asm -r
