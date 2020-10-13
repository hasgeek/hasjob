#!/bin/sh
set -e
export FLASK_ENV="TESTING"
if [ -f secrets.test ]; then
  source ./secrets.test
fi
if [ $# -eq 0 ]; then
    pytest --cov=hasjob
else
    pytest "$@"
fi
