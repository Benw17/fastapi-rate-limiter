from fastapi import FastAPI, Depends
from fastapi_rate_limiter import RateLimiter, rate_limit_middleware, rate_limit_dependency, MemoryStorage

# Create the FastAPI app
app = FastAPI()

# Initialize the rate limiter with in-memory storage.
# default_rate applies to any route that doesn't have a specific rate limit.
app.state.limiter = RateLimiter(MemoryStorage(), default_rate="30/min")

# Apply a global rate limit across all routes.
# Example: no client can make more than 100 requests per minute in total.
rate_limit_middleware(app, rate="100/min")

# Public endpoint
# Uses the global rate limit (30/min fallback if not overridden)
@app.get("/public")
async def public():
    return {"msg": "ok"}

# Login endpoint
# Stricter limit (5 requests/min per IP) to prevent brute-force attacks
@app.get("/login", dependencies=[Depends(rate_limit_dependency("5/min"))])
async def login():
    return {"msg": "login ok"}
