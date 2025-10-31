#!/bin/sh -e
set -x

ruff check app scripts tests --unsafe-fixes --fix
ruff format app scripts tests

set +x