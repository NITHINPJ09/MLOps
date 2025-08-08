#!/bin/bash
set -e
if [ -d "/tmp/prometheus" ]; then
    echo "Directory /tmp/prometheus exists. Clearing contents..."
    rm -rf /tmp/prometheus/*
else
    echo "Creating /tmp/prometheus directory..."
    mkdir -p /tmp/prometheus
fi
exec "$@"