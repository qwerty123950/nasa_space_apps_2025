#!/usr/bin/env bash
set -e
echo "Creating conda env..."
mamba env create -f backend/env.yml || mamba env update -f backend/env.yml
echo "Installing pre-commit..."
mamba run -n weather pip install pre-commit
pre-commit install
echo "Done."