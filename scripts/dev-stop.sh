#!/bin/bash
echo "Stopping Verdis/AegisOS Local Development Environment"
docker compose -f docker-compose.dev.yml down
echo "All services stopped"
