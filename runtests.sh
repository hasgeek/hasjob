#!/bin/sh
set -e
export PYTHONIOENCODING="UTF-8"
export FLASK_ENV="TESTING"
coverage run -m pytest "$@"
coverage report -m
