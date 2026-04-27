## Day X — Firewalls, NAT, and Network Security

### 1. Checking Private IP Address

Command:
ip addr show

Purpose:
Displays all network interfaces and assigned IP addresses.

Example interface:
eth0 → 172.31.84.182

Common private IP ranges:
10.0.0.0 – 10.255.255.255
172.16.0.0 – 172.31.255.255
192.168.0.0 – 192.168.255.255

Private IPs are used inside local networks and are not directly reachable from the internet.

---

### 2. Firewall Configuration with UFW

UFW (Uncomplicated Firewall) is a Linux tool used to control inbound and outbound traffic.

Check firewall status:
sudo ufw status

Allow essential services:

sudo ufw allow 22/tcp    # SSH remote access
sudo ufw allow 80/tcp    # HTTP web traffic
sudo ufw allow 443/tcp   # HTTPS secure web traffic

Enable firewall:
sudo ufw enable

This ensures only required ports are open.

---

### 3. Testing Ports with Netcat

Command:
nc -zv localhost 8888

Flags:
-z → scan mode (no data sent)
-v → verbose output

Purpose:
Check if a port is open or closed.

Possible results:

Connection succeeded
→ Service is listening on the port

Connection refused
→ No service running

Timeout
→ Firewall blocking the port

---

### 4. NAT (Network Address Translation)

NAT allows devices in a private network to access the internet using a shared public IP.

Example flow:

Private device → Router → Internet

The router translates the private IP into a public IP before sending traffic outside the network.

Benefits:
- conserves public IP addresses
- hides internal network structure
- adds a layer of security

---

### 5. Docker Networking Basics

Docker creates a virtual network inside the host machine.

Default Docker network:
172.17.0.0/16

Example:

Host machine
172.31.84.182

Docker bridge
172.17.0.1

Containers receive private IPs such as:
172.17.0.2
172.17.0.3

Containers communicate through the Docker bridge.

Port exposure example:

docker run -p 5000:5000 mycontainer

This maps:

Host port 5000 → Container port 5000

This is NAT occurring inside the host machine.

---

### 6. Server Hardening Concept

When deploying a production server, only essential ports should be open.

Typical configuration:

22/tcp   → SSH
80/tcp   → HTTP
443/tcp  → HTTPS

All other ports should remain closed.

Example rule set:

sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

This reduces the attack surface of the server.