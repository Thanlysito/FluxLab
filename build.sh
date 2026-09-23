#!/usr/bin/env bash
# Lo corre Render en cada deploy.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
