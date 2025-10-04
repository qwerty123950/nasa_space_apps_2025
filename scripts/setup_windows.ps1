Write-Output "Set up Python venv and install backend requirements"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install pre-commit
pre-commit install