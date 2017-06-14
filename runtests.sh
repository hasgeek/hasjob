#!/bin/sh
set -e
export FLASK_ENV="TESTING"
coverage run `which nosetests -v tests`
coverage report
