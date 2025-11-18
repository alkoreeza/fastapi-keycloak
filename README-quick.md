Quick run (assumes Keycloak + MySQL already up and on network keycloak_default):

# Build & start FastAPI
docker compose up -d --build

# Check logs
docker logs -f fastapi

# Test realm connectivity from container:
docker exec -it fastapi curl -s http://keycloak:8080/realms/myrealm | jq .

# Get token (example)
curl -s -X POST "http://localhost:8080/realms/myrealm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=fastapi-client&username=alice&password=alice123" | jq .

# Call protected API
curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://localhost:9000/private