## Debugging Cheat Sheet — Networking & API Issues

### 1. Connection Refused
Meaning:
The target machine is reachable, but no service is listening on the port.

Symptoms:
curl: (7) Failed to connect / Connection refused

Diagnosis:
- Check if service is running:
  lsof -i :5000
  ps aux | grep python

- Check correct port

Fix:
- Start the service
- Ensure app is listening on correct port
- Ensure app is bound to correct host (0.0.0.0 vs localhost)

---

### 2. Timeout
Meaning:
Request sent but no response received.

Symptoms:
curl hangs or times out

Diagnosis:
- Check firewall rules:
  sudo ufw status

- Check port exposure (especially Docker):
  docker ps

- Check network connectivity:
  ping <host>

Fix:
- Open required port in firewall
- Ensure container port is exposed (-p flag)
- Ensure server reachable

---

### 3. DNS Failure
Meaning:
Domain name cannot be resolved to an IP.

Symptoms:
Could not resolve host

Diagnosis:
- Test DNS resolution:
  nslookup example.com

Fix:
- Check domain spelling
- Ensure domain exists
- Check DNS server configuration

---

### 4. CORS Error
Meaning:
Browser blocked request due to cross-origin policy.

Symptoms:
Blocked by CORS policy in browser console

Diagnosis:
- Check browser console
- Check response headers:
  Access-Control-Allow-Origin

Fix:
- Enable CORS in backend

Example (Flask):
  from flask_cors import CORS
  CORS(app, resources={r"/*": {"origins": "*"}})

---

### 5. SSL / HTTPS Error
Meaning:
Secure connection failed.

Symptoms:
SSL error, certificate warning

Diagnosis:
- Check certificate validity
- Verify HTTPS endpoint:
  curl -k https://localhost:5000

Fix:
- Use valid certificate
- For local dev, allow self-signed (-k flag)
- Ensure HTTPS correctly configured

---

### Quick Mental Model

Error Type → Likely Problem

Connection refused → Service not running
Timeout → Firewall / network issue
DNS failure → Domain issue
CORS error → Missing headers
SSL error → Certificate / HTTPS issue 