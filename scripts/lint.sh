#!/usr/bin/env sh

# Enable tracing for debugging
set -x

# Run mypy, ruff, and other commands
mypy src
ruff check src scripts
ruff format src scripts  --check
# Disable tracing after the main commands
set +x
