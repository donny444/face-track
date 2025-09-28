@echo off
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%.venv"

if not defined PYTHON_BIN set "PYTHON_BIN=python"

where %PYTHON_BIN% >nul 2>&1
if errorlevel 1 (
	where python3 >nul 2>&1
	if errorlevel 1 (
		echo Error: python interpreter not found. Set PYTHON_BIN to a valid executable.
		exit /b 1
	) else (
		set "PYTHON_BIN=python3"
	)
)

echo Using Python interpreter: %PYTHON_BIN%

if not exist "%VENV_DIR%" (
	echo Creating virtual environment at %VENV_DIR%
	%PYTHON_BIN% -m venv "%VENV_DIR%"
) else (
	echo Virtual environment already exists at %VENV_DIR%
)

call "%VENV_DIR%\Scripts\activate.bat"

echo Upgrading pip
python -m pip install --upgrade pip

set "REQ_FILE=%PROJECT_ROOT%requirements.txt"
if exist "%REQ_FILE%" (
	echo Installing dependencies from %REQ_FILE%
	python -m pip install -r "%REQ_FILE%"
) else (
	echo No requirements.txt found at %REQ_FILE%; skipping dependency installation
)

call deactivate

echo Virtual environment is ready in %VENV_DIR%

endlocal
