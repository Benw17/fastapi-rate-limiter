# fastapi-rate-limiter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A simple and flexible **rate limiting library for FastAPI** with support for in-memory and Redis storage.

---

## Why Use fastapi-rate-limiter?

Rate limiting is highly essential for cyber-security and protecting your FastAPI application from abuse, brute-force attacks, and high traffic spikes. This library provides:

* Easy global and per-route limits
* IP-based isolation
* Async-safe implementation
* Option to use Redis for multi-instance deployments
* Lightweight, easy to integrate

---

## Features

* **Global rate limiting middleware**
* **Per-route rate limiting via dependency**
* **IP-based rate isolation**
* **Configurable time windows and request limits**
* **In-memory or Redis storage backend**
* **Async-safe for FastAPI endpoints**

---

## Installation

Install from PyPI:

```bash
pip install fastapi-rate-limiter
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/yourusername/fastapi-rate-limiter.git
```

---

## How to Use

### 1. Setup the Rate Limiter

```python
from fastapi import FastAPI
from fastapi_rate_limiter import RateLimiter
from fastapi_rate_limiter.storage import MemoryStorage

app = FastAPI()

# Initialize limiter with MemoryStorage
app.state.limiter = RateLimiter(storage=MemoryStorage(), default_rate="3/min")
```

**Why:** Provides the core limiter logic and a storage backend for counting requests. Attaching it to `app.state.limiter` makes it accessible everywhere in the app.

---

### 2. Apply Global Middleware

```python
from fastapi_rate_limiter import rate_limit_middleware

rate_limit_middleware(app, rate="10/min")
```

**Why:** Protects the app with a global limit to prevent traffic spikes or abuse, independent of per-route settings.

---

### 3. Per-Route Rate Limiting

```python
from fastapi import Depends
from fastapi_rate_limiter import rate_limit_dependency

@app.get("/login", dependencies=[Depends(rate_limit_dependency("2/min"))])
async def login():
    return {"msg": "login"}
```

**Why:** Some routes (e.g. login endpoints) need stricter limits than the global middleware. Dependencies allow fine-grained control. These can help prevent brute force attacks.

---

### 4. IP-Based Isolation

* Each client IP has independent counters.

**Why:** Prevents one client from exhausting the rate limit for everyone else.

---

### 5. Using Redis for Multi-Instance Apps

```python
from fastapi_rate_limiter.storage import RedisStorage
from redis.asyncio import Redis

redis_client = Redis(host="localhost", port=6379, db=0)
app.state.limiter = RateLimiter(storage=RedisStorage(redis_client), default_rate="3/min")
```

**Why:** Memory storage only works per instance. Redis ensures limits are shared across multiple servers. 

## Note: This uses **Redis** to replace local memory and can be ignored if you don't use multiple servers.


---

## Testing Your Setup

```bash
pytest -v
```

Tests ensure:

* Global and per-route limits
* IP isolation
* Concurrency handling
* Window resets

---

## Contributing

Contributions are welcome! Steps:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

Or email me at **[whitb20@yahoo.com.au](mailto:whitb20@yahoo.com.au)** for suggestions.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Planned Improvements
* API key-based rate limiting 
* Detailed examples and tutorials
* Extended test coverage and edge cases

---

## Links

* [Project Homepage](https://github.com/Benw17/fastapi-rate-limiter)
