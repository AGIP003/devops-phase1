## Day X — CORS & API Security Basics

### 1. What is CORS
CORS (Cross-Origin Resource Sharing) is a browser security mechanism that controls how web pages access resources from a different origin.

An origin consists of:
scheme + domain + port

Example:
Frontend → http://localhost:3000
Backend  → https://localhost:5000

Since these differ in protocol and port, the browser treats them as different origins and blocks requests unless the server explicitly allows them.

---

### 2. How CORS Works
When a frontend requests data from another origin, the browser checks the server response for permission headers.

Example response headers:

Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type

These headers tell the browser that the request is allowed.

---

### 3. Preflight Requests
For certain requests (POST, PUT, DELETE, or requests with custom headers), the browser first sends a preflight request using the OPTIONS method.

Example:

OPTIONS /transactions
Origin: http://localhost:3000
Access-Control-Request-Method: GET

The server must respond with CORS headers or the browser blocks the request.

---

### 4. Implementing CORS in Flask

from flask_cors import CORS

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}}
)

This allows requests from the React frontend running on http://localhost:3000.

The rule r"/*" applies CORS headers to all API routes.

---

### 5. Testing CORS with curl

curl -k -X OPTIONS https://localhost:5000/transactions \
-H "Origin: http://localhost:3000" \
-H "Access-Control-Request-Method: GET" -v

This verifies:
- TLS/HTTPS connection
- endpoint availability
- correct handling of OPTIONS requests
- proper CORS configuration

---

### 6. Testing from Browser Console

fetch('https://localhost:5000/transactions')
  .then(r => r.json())
  .then(console.log)

If CORS is configured correctly, the response is accessible from the frontend.

---

### 7. API Security Basics

HTTPS (TLS)
All API communication should be encrypted using HTTPS to prevent interception. In this project a self-signed certificate was used for local development.

Origin Control
CORS restricts which frontends can access the backend API.

Preflight Validation
Browsers verify permissions before sending sensitive requests using OPTIONS preflight checks.

API Boundary Protection
The backend defines allowed origins, methods, and headers to reduce the API attack surface.

---

### Tools Used
Flask
Flask-CORS
curl
Browser developer console
HTTPS / TLS