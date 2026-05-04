# Makefile

# Specify the Python version
PYTHON_VERSION := python
LAMBDA_VENV := .lambda_venv
PACKAGE_NAME := lambda_package.zip
LAMBDA_FUNCTION := lambda_code.py # Add other files separated by spaces if necessary

# Default target executed when no arguments are given to make.
default: clean package

# Setup a virtual environment
venv:
	$(PYTHON_VERSION) -m venv $(LAMBDA_VENV)
	$(LAMBDA_VENV)\Scripts\pip install -U pip

# Install dependencies into the virtual environment
dependencies: venv
	$(LAMBDA_VENV)\Scripts\pip install -r lambda/requirements.txt

# Package the virtual environment libraries and your lambda function into a zip
package: dependencies
	powershell -Command "Compress-Archive -Path $(LAMBDA_VENV)\Lib\site-packages\* -DestinationPath $(PACKAGE_NAME) -Force"
	powershell -Command "Compress-Archive -Path lambda\$(LAMBDA_FUNCTION) -DestinationPath $(PACKAGE_NAME) -Update"

# Clean up the environment
clean:
	rmdir /s /q $(LAMBDA_VENV) 2>nul || true
	del /q $(PACKAGE_NAME) 2>nul || true

.PHONY: default venv dependencies package clean