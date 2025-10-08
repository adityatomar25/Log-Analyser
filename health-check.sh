#!/bin/bash

echo "=== Docker Container Health Check ==="
echo "Checking container status..."
docker-compose ps

echo -e "\n=== API Endpoint Health Check ==="
echo "Testing backend health..."
curl -s http://localhost:8000/api/auth/status | jq . 2>/dev/null || curl -s http://localhost:8000/api/auth/status

echo -e "\n\nTesting frontend accessibility..."
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
echo "Frontend HTTP status: $frontend_status"

echo -e "\n=== Authentication Test ==="
echo "Testing login functionality..."
login_response=$(curl -s -X POST -d 'username=admin&password=password' http://localhost:8000/login)
echo "Login response: $login_response"

echo -e "\n=== Recent Logs ==="
echo "Last 5 lines from each container:"
echo "--- Backend ---"
docker logs log-analyser-backend --tail=5
echo "--- Frontend ---"
docker logs log-analyser-frontend --tail=5

echo -e "\n=== Summary ==="
if [ "$frontend_status" = "200" ]; then
    echo "✅ Frontend is accessible at http://localhost:3000"
else
    echo "❌ Frontend is not accessible"
fi

if echo "$login_response" | grep -q "Login successful"; then
    echo "✅ Backend API and authentication are working"
else
    echo "❌ Backend API issues detected"
fi
