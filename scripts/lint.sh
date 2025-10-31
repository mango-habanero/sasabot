#!/usr/bin/env sh

# Enable tracing for debugging
set -x

# Run mypy, ruff, and other commands
mypy src
ruff check app scripts
ruff format app scripts  --check
# Disable tracing after the main commands
set +x
