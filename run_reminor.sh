#!/usr/bin/env bash

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
REQUIREMENTS_FILE="${PROJECT_DIR}/requirements.txt"
SPACY_MODEL="it_core_news_md"
PYTHON_EXEC="python3"
ENV_FILE="${PROJECT_DIR}/.env"
ENV_TEMPLATE_FILE="${PROJECT_DIR}/.env.template"

info() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_python_pip() {
    info "Checking for Python 3 and pip..."
    if ! command_exists ${PYTHON_EXEC}; then
        error "${PYTHON_EXEC} is not installed or not in PATH. Please install Python 3."
    fi
    if ! ${PYTHON_EXEC} -m pip --version >/dev/null 2>&1; then
        info "pip for ${PYTHON_EXEC} not found. Attempting to ensure pip..."
        if ! ${PYTHON_EXEC} -m ensurepip --upgrade >/dev/null 2>&1; then
            error "pip is not available for ${PYTHON_EXEC}. Please install pip (e.g., sudo apt install python3-pip on Debian/Ubuntu, or ensure it's installed with your Python distribution)."
        fi
        info "pip for ${PYTHON_EXEC} should now be available."
    fi
    info "Python 3 and pip are available."
}

setup_venv() {
    info "Checking for virtual environment at ${VENV_DIR}..."
    if [ ! -d "${VENV_DIR}" ]; then
        info "Virtual environment not found. Creating one using '${PYTHON_EXEC} -m venv'..."
        ${PYTHON_EXEC} -m venv "${VENV_DIR}"
        if [ $? -ne 0 ]; then
            error "Failed to create virtual environment. Make sure '${PYTHON_EXEC} -m venv' is working (e.g., install python3-venv package on Debian/Ubuntu)."
        fi
        info "Virtual environment created successfully at ${VENV_DIR}."
    else
        info "Virtual environment already exists at ${VENV_DIR}."
    fi
}

activate_venv() {
    info "Activating virtual environment..."
    # shellcheck disable=SC1090
    source "${VENV_DIR}/bin/activate"
    if [ $? -ne 0 ]; then
        error "Failed to activate virtual environment."
    fi
    info "Virtual environment activated. Python executable: $(which python)"
}

install_requirements() {
    info "Checking and installing requirements from ${REQUIREMENTS_FILE}..."
    if [ ! -f "${REQUIREMENTS_FILE}" ]; then
        error "${REQUIREMENTS_FILE} not found at ${PROJECT_DIR}."
    fi
    ${PYTHON_EXEC} -m pip install -r "${REQUIREMENTS_FILE}"
    if [ $? -ne 0 ]; then
        error "Failed to install requirements from ${REQUIREMENTS_FILE}."
    fi
    info "Requirements installed successfully."
}

check_scikit_learn() {
    info "Verifying scikit-learn installation..."
    if ! ${PYTHON_EXEC} -c "import sklearn" >/dev/null 2>&1; then
        info "scikit-learn not found, installing..."
        ${PYTHON_EXEC} -m pip install scikit-learn >/dev/null 2>&1 || true
    fi
}

install_spacy_model() {
    info "Checking for spaCy model '${SPACY_MODEL}'..."
    if ${PYTHON_EXEC} -c "import spacy; spacy.load('${SPACY_MODEL}')" >/dev/null 2>&1; then
        info "spaCy model '${SPACY_MODEL}' is already installed and valid."
    else
        info "spaCy model '${SPACY_MODEL}' not found or invalid. Downloading..."
        ${PYTHON_EXEC} -m spacy download "${SPACY_MODEL}"
        if [ $? -ne 0 ]; then
            error "Failed to download spaCy model '${SPACY_MODEL}'. Make sure you have internet access and spacy is installed correctly."
        fi
        if ! ${PYTHON_EXEC} -c "import spacy; spacy.load('${SPACY_MODEL}')" >/dev/null 2>&1; then
             error "spaCy model '${SPACY_MODEL}' downloaded but still not loading correctly. Please check spaCy installation and model."
        fi
        info "spaCy model '${SPACY_MODEL}' downloaded and verified successfully."
    fi
}

check_and_setup_env_file() {
    info "Checking for .env file at ${ENV_FILE}..."
    if [ ! -f "${ENV_FILE}" ]; then
        if [ -f "${ENV_TEMPLATE_FILE}" ]; then
            info "Creating .env file from template..."
            cp "${ENV_TEMPLATE_FILE}" "${ENV_FILE}"
            info ".env file created at ${ENV_FILE}."
        else
            error ".env file not found and no .env.template available at ${ENV_TEMPLATE_FILE}."
        fi
    else
        info ".env file already exists at ${ENV_FILE}."
    fi
}

run_application() {
    info "Starting Reminor application (reminor.py) using $(which ${PYTHON_EXEC})..."
    ${PYTHON_EXEC} reminor.py
    
    local exit_status=$?
    if [ ${exit_status} -ne 0 ]; then
        info "Reminor application exited with status ${exit_status}."
    else
        info "Reminor application finished successfully."
    fi
}

main() {
    info "=== Reminor Application Setup & Run Script ==="
    cd "${PROJECT_DIR}"

    check_python_pip
    setup_venv
    activate_venv
    install_requirements
    check_scikit_learn
    install_spacy_model
    check_and_setup_env_file
    run_application

    info "=== Script finished. ==="
}

main
