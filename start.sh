#!/bin/bash
# start.sh - Enforces the correct startup sequence for the meeting application

echo -e "\e[32mStarting database services...\e[0m"
docker-compose up -d postgres auth-db redis
echo -e "\e[33mWaiting for database services to be ready (15 seconds)...\e[0m"
sleep 15

echo -e "\e[32mStarting authentication service...\e[0m"
docker-compose up -d auth-service
echo -e "\e[33mWaiting for authentication service to initialize (10 seconds)...\e[0m"
sleep 10

echo -e "\e[32mStarting backend service...\e[0m"
docker-compose up -d backend
echo -e "\e[33mWaiting for backend service to initialize (10 seconds)...\e[0m"
sleep 10

echo -e "\e[32mStarting websocket service...\e[0m"
docker-compose up -d websocket
echo -e "\e[33mWaiting for websocket service to initialize (5 seconds)...\e[0m"
sleep 5

echo -e "\e[32mStarting frontend service...\e[0m"
docker-compose up -d frontend

echo -e "\e[32mStarting monitoring services...\e[0m"
docker-compose up -d prometheus grafana

echo -e "\e[36mAll services started. Check status with: docker-compose ps\e[0m"
docker-compose ps

echo -e "\e[32mApplication is now available at:\e[0m"
echo -e "\e[36m  Frontend: http://localhost:3000\e[0m"
echo -e "\e[36m  Backend API: http://localhost:5000\e[0m"
echo -e "\e[36m  Auth API: http://localhost:5001\e[0m"
echo -e "\e[36m  WebSocket: http://localhost:3001\e[0m"
echo -e "\e[36m  Prometheus: http://localhost:9090\e[0m"
echo -e "\e[36m  Grafana: http://localhost:3002\e[0m" 