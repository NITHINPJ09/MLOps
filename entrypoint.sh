#!/bin/bash
set -e
rm -rf /tmp/metrics && mkdir /tmp/metrics
exec gunicorn --bind 0.0.0.0:8000 --workers 2 app:app