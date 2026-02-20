#!/bin/bash

BASE_URL="http://127.0.0.1:5000"

echo " Starting API Logic Test. "

# 1. CREATE
echo -e "\n1. Testing POST (Create)..."
CREATE_RES=$(curl -s -X POST "$BASE_URL/transactions" \
     -H "Content-Type: application/json" \
     -d '{"date": "2026-02-11", "amount": 50.0, "type": "expense", "category": "food", "description": "Pizza Party", "payment_method": "cash"}')
echo $CREATE_RES

# Extract ID for next steps  search for "id" then grab the number between quotes
ID=$(echo $CREATE_RES | sed -n 's/.*"id":\s*"\([^"]*\)".*/\1/p')
echo "Captured ID: $ID"

# 2. SEARCH
echo -e "\n2. Testing GET (Search for 'Pizza')..."
curl -s -G "$BASE_URL/transactions" --data-urlencode "query=Pizza"

# 3. UPDATE
echo -e "\n3. Testing PUT (Update amount)..."
curl -s -X PUT "$BASE_URL/transactions/$ID" \
     -H "Content-Type: application/json" \
     -d "{\"field\": \"amount\", \"updates\": 75.0}"

# 4. DELETE
echo -e "\n4. Testing DELETE..."
curl -s -X DELETE "$BASE_URL/transactions/$ID"

echo -e "\n Test Cycle Complete!"
