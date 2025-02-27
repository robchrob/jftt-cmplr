# Makefile
.PHONY: build test profile clean

# Default target
all: build test

# Build target (nothing to build for Python, but we can check syntax)
build:
	python -m py_compile main.py
	python -m py_compile vm.py
	python -m py_compile compiler/*.py
	python -m py_compile tests/*.py
	@echo "Build successful"

# Run all tests
test:
	python -m tests.test_runner

# Run performance profiling
profile:
	python -m tests.profiler

# Clean target
clean:
	rm -f *.pyc compiler/*.pyc vm/*.pyc tests/*.pyc
	rm -rf __pycache__ compiler/__pycache__ vm/__pycache__ tests/__pycache__
	@echo "Cleaned up generated files"

