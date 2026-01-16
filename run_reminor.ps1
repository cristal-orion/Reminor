# PowerShell script to run Reminor on Windows
# Exit on any error
$ErrorActionPreference = "Stop"

# Define project directory and venv directory
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_DIR = Join-Path $PROJECT_DIR "venv"
$REQUIREMENTS_FILE = Join-Path $PROJECT_DIR "requirements.txt"
$SPACY_MODEL = "it_core_news_md"
$PYTHON_EXEC = "python"
$ENV_FILE = Join-Path $PROJECT_DIR ".env"
$ENV_TEMPLATE_FILE = Join-Path $PROJECT_DIR ".env.template"

# Function to print informational messages
function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

# Function to print error messages and exit
function Write-Error-Exit {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Step 0: Check for Python 3 and pip
function Test-PythonPip {
    Write-Info "Checking for Python 3 and pip..."
    if (-not (Test-Command $PYTHON_EXEC)) {
        Write-Error-Exit "$PYTHON_EXEC is not installed or not in PATH. Please install Python 3."
    }
    
    # Check if pip module is available
    try {
        & $PYTHON_EXEC -m pip --version | Out-Null
    }
    catch {
        Write-Info "pip for $PYTHON_EXEC not found. Attempting to ensure pip..."
        try {
            & $PYTHON_EXEC -m ensurepip --upgrade | Out-Null
        }
        catch {
            Write-Error-Exit "pip is not available for $PYTHON_EXEC. Please install pip."
        }
        Write-Info "pip for $PYTHON_EXEC should now be available."
    }
    Write-Info "Python 3 and pip are available."
}

# Step 1: Check if virtual environment exists, create it if missing
function Setup-Venv {
    Write-Info "Checking for virtual environment at $VENV_DIR..."
    $ACTIVATE_SCRIPT = Join-Path $VENV_DIR "Scripts\Activate.ps1"
    
    if (-not (Test-Path $VENV_DIR) -or -not (Test-Path $ACTIVATE_SCRIPT)) {
        if (Test-Path $VENV_DIR) {
            Write-Info "Virtual environment exists but is incompatible with Windows. Recreating..."
            Remove-Item $VENV_DIR -Recurse -Force
        }
        Write-Info "Creating virtual environment using '$PYTHON_EXEC -m venv'..."
        try {
            & $PYTHON_EXEC -m venv $VENV_DIR
        }
        catch {
            Write-Error-Exit "Failed to create virtual environment. Make sure '$PYTHON_EXEC -m venv' is working."
        }
        Write-Info "Virtual environment created successfully at $VENV_DIR."
    }
    else {
        Write-Info "Virtual environment already exists at $VENV_DIR."
    }
}

# Step 2: Activate the virtual environment
function Activate-Venv {
    Write-Info "Activating virtual environment..."
    $ACTIVATE_SCRIPT = Join-Path $VENV_DIR "Scripts\Activate.ps1"
    if (-not (Test-Path $ACTIVATE_SCRIPT)) {
        Write-Error-Exit "Failed to find activation script at $ACTIVATE_SCRIPT"
    }
    
    try {
        & $ACTIVATE_SCRIPT
    }
    catch {
        Write-Error-Exit "Failed to activate virtual environment."
    }
    
    # Update Python executable to use the venv one
    $script:PYTHON_EXEC = Join-Path $VENV_DIR "Scripts\python.exe"
    Write-Info "Virtual environment activated. Python executable: $PYTHON_EXEC"
}

# Step 3: Check if requirements are installed, install them if missing
function Install-Requirements {
    Write-Info "Checking and installing requirements from $REQUIREMENTS_FILE..."
    if (-not (Test-Path $REQUIREMENTS_FILE)) {
        Write-Error-Exit "$REQUIREMENTS_FILE not found at $PROJECT_DIR."
    }
    
    try {
        & $PYTHON_EXEC -m pip install -r $REQUIREMENTS_FILE
    }
    catch {
        Write-Error-Exit "Failed to install requirements from $REQUIREMENTS_FILE."
    }
    Write-Info "Requirements installed successfully."
}

# Step 3.5: Ensure scikit-learn is available
function Test-ScikitLearn {
    Write-Info "Verifying scikit-learn installation..."
    try {
        & $PYTHON_EXEC -c "import sklearn" 2>$null
    }
    catch {
        Write-Info "scikit-learn not found, installing..."
        try {
            & $PYTHON_EXEC -m pip install scikit-learn 2>$null
        }
        catch {
            # Silently continue if installation fails
        }
    }
}

# Step 4: Check if spaCy Italian model is installed, download it if missing
function Install-SpacyModel {
    Write-Info "Checking for spaCy model '$SPACY_MODEL'..."
    
    try {
        & $PYTHON_EXEC -c "import spacy; spacy.load('$SPACY_MODEL')" 2>$null
        Write-Info "spaCy model '$SPACY_MODEL' is already installed and valid."
    }
    catch {
        Write-Info "spaCy model '$SPACY_MODEL' not found or invalid. Downloading..."
        try {
            & $PYTHON_EXEC -m spacy download $SPACY_MODEL
        }
        catch {
            Write-Error-Exit "Failed to download spaCy model '$SPACY_MODEL'. Make sure you have internet access and spacy is installed correctly."
        }
        
        # Validate after download
        try {
            & $PYTHON_EXEC -c "import spacy; spacy.load('$SPACY_MODEL')" 2>$null
        }
        catch {
            Write-Error-Exit "spaCy model '$SPACY_MODEL' downloaded but still not loading correctly. Please check spaCy installation and model."
        }
        Write-Info "spaCy model '$SPACY_MODEL' downloaded and verified successfully."
    }
}

# Step 4.5: Check for .env file and create from template if needed
function Test-SetupEnvFile {
    Write-Info "Checking for .env file at $ENV_FILE..."
    if (-not (Test-Path $ENV_FILE)) {
        if (Test-Path $ENV_TEMPLATE_FILE) {
            Write-Info ".env file not found. Creating from template at $ENV_TEMPLATE_FILE..."
            Copy-Item $ENV_TEMPLATE_FILE $ENV_FILE
            Write-Info ".env file created from template. Please edit $ENV_FILE with your configuration values before running the application."
        }
        else {
            Write-Info ".env file and template not found. Please create $ENV_FILE manually with required configuration values."
        }
    }
    else {
        Write-Info ".env file already exists at $ENV_FILE."
    }
}

# Step 4.6: Load environment variables from .env file
function Load-EnvFile {
    Write-Info "Loading environment variables from .env file..."
    if (Test-Path $ENV_FILE) {
        Get-Content $ENV_FILE | ForEach-Object {
            if ($_ -match '^([^#][^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove quotes if present
                if ($value -match '^"(.*)"$' -or $value -match "^'(.*)'$") {
                    $value = $matches[1]
                }
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Info "Loaded environment variable: $name"
            }
        }
    }
    else {
        Write-Info ".env file not found, skipping environment variable loading."
    }
}

# Step 5: Run the Reminor application
function Start-Application {
    Write-Info "Starting Reminor application (reminor.py) using $PYTHON_EXEC..."
    try {
        & $PYTHON_EXEC reminor.py
        $exitStatus = $LASTEXITCODE
        if ($exitStatus -ne 0) {
            Write-Info "Reminor application exited with status $exitStatus."
        }
        else {
            Write-Info "Reminor application finished successfully."
        }
    }
    catch {
        Write-Error-Exit "Failed to start Reminor application."
    }
}

# Main script execution
function Main {
    Write-Info "=== Reminor Application Setup & Run Script ==="
    
    # Ensure the script is in the project's root directory
    Set-Location $PROJECT_DIR
    
    # Execute steps
    Test-PythonPip
    Setup-Venv
    Activate-Venv
    Install-Requirements
    Test-ScikitLearn
    Install-SpacyModel
    Test-SetupEnvFile
    Load-EnvFile
    Start-Application
    
    Write-Info "=== Script finished. ==="
}

# Call the main function to start the script
Main