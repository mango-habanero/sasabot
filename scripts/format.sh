#!/bin/sh -e
set -x

ruff check src scripts tests --unsafe-fixes --fix
ruff format src scripts tests

set +x