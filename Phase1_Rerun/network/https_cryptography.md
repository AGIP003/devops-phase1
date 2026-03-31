# HTTPS, SSL/TLS, and Cryptography — Notes

This section explores how secure communication works on the web, focusing on encryption, TLS certificates, and HTTPS configuration.

---

# 1. Cryptography Basics

Cryptography protects data by transforming it into an unreadable format that can only be decoded with the correct key.

Main goals of cryptography:

* **Confidentiality** — data cannot be read by unauthorized parties
* **Integrity** — data cannot be altered without detection
* **Authentication** — identity of communicating parties can be verified

Cryptography is the foundation of secure internet communication.

---

# 2. Symmetric Encryption

Symmetric encryption uses **one shared secret key** for both encryption and decryption.

Example process:

```
Plaintext → Encrypt (secret key) → Ciphertext
Ciphertext → Decrypt (same secret key) → Plaintext
```

Characteristics:

* Very **fast**
* Used for encrypting large amounts of data
* Requires secure key sharing

Common symmetric algorithms:

* AES (Advanced Encryption Standard)
* ChaCha20

Example usage in TLS:

Once a secure connection is established, symmetric encryption protects the actual data transfer.

---

# 3. Asymmetric Encryption (Public / Private Keys)

Asymmetric encryption uses **two different keys**.

```
Public Key  → shared with everyone
Private Key → kept secret
```

How it works:

* Data encrypted with the **public key** can only be decrypted with the **private key**.

Example:

```
Client encrypts message using server's public key
Server decrypts using its private key
```

Common algorithms:

* RSA
* Elliptic Curve Cryptography (ECC)

Asymmetric encryption is slower than symmetric encryption but solves the **key exchange problem**.

---

# 4. SSL vs TLS

SSL and TLS are protocols that secure communication over networks.

| Protocol | Status          |
| -------- | --------------- |
| SSL      | Deprecated      |
| TLS      | Modern standard |

TLS replaced SSL and provides stronger encryption and improved security mechanisms.

Modern websites use **TLS 1.2 or TLS 1.3**.

Example secure protocol:

```
HTTPS = HTTP + TLS encryption
```

---

# 5. TLS Handshake

Before encrypted communication begins, a **TLS handshake** occurs.

Simplified process:

1. Client connects to server
2. Server sends its TLS certificate
3. Client verifies certificate authority
4. Client and server agree on encryption methods
5. Session keys are generated
6. Secure communication begins

After the handshake, symmetric encryption is used for performance.

---

# 6. Digital Certificates

A certificate proves the identity of a server.

Certificates contain:

* Domain name
* Public key
* Issuing Certificate Authority
* Expiration date
* Digital signature

Example certificate chain:

```
Server Certificate
   ↓
Intermediate Certificate Authority
   ↓
Root Certificate Authority
```

Browsers trust certificates signed by recognized root authorities.

Common Certificate Authorities include organizations such as:

* Let's Encrypt
* DigiCert
* Sectigo

---

# 7. Self-Signed Certificates

A self-signed certificate is created and signed by the same entity.

Example command used in this lab:

```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

This command:

* generates a private key
* creates a certificate
* signs the certificate locally

Self-signed certificates are useful for:

* local development
* testing HTTPS
* internal systems

Browsers do not trust them automatically because no trusted certificate authority verifies them.

---

# 8. Running Flask with HTTPS (Local Testing)

After generating the certificate and key, Flask can run over HTTPS.

Example:

```
app.run(ssl_context=('cert.pem', 'key.pem'))
```

This starts the Flask server using TLS encryption.

The server becomes accessible via:

```
https://localhost:5000
```

Browsers will show a warning because the certificate is self-signed.

---

# 9. Security Best Practices

Important practices when handling certificates:

* Never commit private keys to Git repositories
* Store keys securely with restricted access
* Use trusted certificate authorities in production
* Rotate certificates regularly

In production systems, HTTPS is typically handled by reverse proxies such as Nginx rather than application frameworks.

---

# Key Takeaways

* HTTPS secures HTTP communication using TLS encryption.
* Symmetric encryption protects data transfer after a connection is established.
* Asymmetric encryption enables secure key exchange.
* Digital certificates verify the identity of servers.
* Self-signed certificates are useful for local testing but not trusted in production.
