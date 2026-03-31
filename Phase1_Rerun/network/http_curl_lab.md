# HTTP Requests with `curl` — Summary

This lab explored how HTTP communication works using the `curl` command-line tool. The goal was to understand how clients interact with servers, inspect HTTP requests and responses, and analyze headers and status codes.

## 1. Making GET Requests

Command used:

```
curl -v https://api.github.com/users/octocat
```

Key points:

* `curl` sends an HTTP request from the terminal.
* `-v` (verbose) shows both the **request headers** sent by the client and the **response headers** returned by the server.
* The server returns data in **JSON format**, indicated by the `Content-Type` header.

This demonstrates how APIs return structured data to clients.

---

## 2. Testing API Endpoints

Commands used:

```
curl http://localhost:5000/transactions
```

```
curl -X POST http://localhost:5000/login \
-H "Content-Type: application/json" \
-d '{"username":"test","password":"test"}'
```

Key points:

* `GET` requests retrieve data from a server.
* `POST` requests send data to a server.
* `-H` sets HTTP headers (e.g., specifying JSON content).
* `-d` sends a request body.

These commands simulate how frontends or other services interact with backend APIs.

---

## 3. Inspecting HTTP Status Codes

Commands used:

```
curl -I https://google.com
curl -I https://github.com/404
```

Key points:

* `-I` fetches only the **response headers**, not the body.
* HTTP status codes communicate the result of a request.

Common examples:

| Status Code | Meaning                         |
| ----------- | ------------------------------- |
| 200         | Request succeeded               |
| 301         | Resource permanently redirected |
| 404         | Resource not found              |
| 500         | Server error                    |

Status codes help clients understand how to handle responses.

---

## 4. Inspecting HTTP Headers

Command used:

```
curl -v https://github.com 2>&1 | grep -i 'content-type\|set-cookie\|cache'
```

Key points:

* `2>&1` merges standard error with standard output so `grep` can filter the verbose output.
* `grep` filters specific headers for easier inspection.

Important headers observed:

* **Content-Type** → indicates the format of the response body.
* **Set-Cookie** → instructs the browser to store session or tracking cookies.
* **Cache-Control** → defines caching behavior for browsers or proxies.

These headers influence how clients process responses, manage sessions, and cache resources.

---

## Key Takeaways

* `curl` allows direct interaction with HTTP servers from the terminal.
* HTTP requests contain methods, headers, and optional bodies.
* Servers respond with status codes, headers, and a response body.
* Headers control important behaviors like **content format, authentication, caching, and sessions**.

This lab builds the foundation for testing APIs, debugging backend services, and understanding how web applications communicate over HTTP.
