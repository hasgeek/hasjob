#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=$PYTHONPATH:$PWD:$PWD/application:$PWD/templates
python -B application/website.py
