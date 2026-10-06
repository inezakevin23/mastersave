#!/usr/bin/env bash
pip install -r requirements.txt
set -o errexit

python manage.py collectstatic --no-input
python manage.py migrate