#!/bin/bash
# Rebuild model registry after discovery scan
python3 /opt/evolvixos/models/build_registry.py >> /var/log/evolvix-registry.log 2>&1
