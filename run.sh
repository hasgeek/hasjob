#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=$PYTHONPATH:$PWD
python -B application/website.py
