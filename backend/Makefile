# Makefile

# Set this to python3, python3.14, or your active virtual environment's python command
PYTHON_VERSION := python3
PACKAGE_DIR := .lambda_package
PACKAGE_NAME := lambda_package.zip
LAMBDA_FUNCTION := lambda_function.py

# Default target executed when no arguments are given to make.
default: clean package

# Install dependencies for Linux x86_64 directly into package dir
dependencies:
	$(PYTHON_VERSION) -m pip install -r requirements.txt \
		--platform manylinux2014_x86_64 \
		--implementation cp \
		--python-version 3.14 \
		--only-binary=:all: \
		--target $(PACKAGE_DIR)

# Package the dependencies and lambda function into a zip
package: dependencies
	cp python_files/$(LAMBDA_FUNCTION) $(PACKAGE_DIR)/
	cd $(PACKAGE_DIR) && zip -r ../$(PACKAGE_NAME) .

# Clean up
clean:
	rm -rf $(PACKAGE_DIR)
	rm -f $(PACKAGE_NAME)

.PHONY: default dependencies package clean