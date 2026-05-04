# Makefile

PYTHON_VERSION := py -3.14
PACKAGE_DIR := .lambda_package
PACKAGE_NAME := lambda_package.zip
LAMBDA_FUNCTION := lambda_code.py # Add other files separated by spaces if necessary

# Default target executed when no arguments are given to make.
default: clean package

# Install dependencies for Linux x86_64 directly into package dir
dependencies:
	$(PYTHON_VERSION) -m pip install -r lambda/requirements.txt \
		--platform manylinux2014_x86_64 \
		--implementation cp \
		--python-version 3.14 \
		--only-binary=:all: \
		--target $(PACKAGE_DIR)

# Package the dependencies and lambda function into a zip
package: dependencies
	copy lambda\$(LAMBDA_FUNCTION) $(PACKAGE_DIR)
	powershell -Command "Compress-Archive -Path $(PACKAGE_DIR)\* -DestinationPath $(PACKAGE_NAME) -Force"

# Clean up
clean:
	-rmdir /s /q $(PACKAGE_DIR) 2>nul
	-del /q $(PACKAGE_NAME) 2>nul

.PHONY: default dependencies package clean
