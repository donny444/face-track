#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
	if command -v python >/dev/null 2>&1; then
		PYTHON_BIN="python"
	else
		echo "Error: python interpreter not found. Set PYTHON_BIN to a valid executable." >&2
		exit 1
	fi
fi

echo "Using Python interpreter: ${PYTHON_BIN}"

if [[ ! -d "${VENV_DIR}" ]]; then
	echo "Creating virtual environment at ${VENV_DIR}"
	"${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
	echo "Virtual environment already exists at ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

echo "Upgrading pip"
python -m pip install --upgrade pip

REQ_FILE="${PROJECT_ROOT}/requirements.txt"
if [[ -f "${REQ_FILE}" ]]; then
	echo "Installing dependencies from ${REQ_FILE}"
	python -m pip install -r "${REQ_FILE}"
else
	echo "No requirements.txt found at ${REQ_FILE}; skipping dependency installation"
fi

deactivate

echo "Virtual environment is ready in ${VENV_DIR}"
