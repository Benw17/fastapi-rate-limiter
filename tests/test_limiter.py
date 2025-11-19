import asyncio
from fastapi import FastAPI, Depends
from fastapi_rate_limiter import RateLimiter, rate_limit_middleware, rate_limit_dependency, MemoryStorage
from httpx import AsyncClient
import pytest
import time


GLOBAL_RATE_LIMIT = 20
LOGIN_RATE_LIMIT = 2
CUSTOM_RATE_LIMIT = 5
ALLOWED_TIME_FOR_WINDOW_RESET = 61


@pytest.fixture
def app():
    app = FastAPI()

    # use small values for tests
    app.state.limiter = RateLimiter(storage=MemoryStorage(), default_rate="3/min")

    # Apply global limiter
    rate_limit_middleware(app, rate=f"{GLOBAL_RATE_LIMIT}/min")

    @app.get("/public")
    async def public():
        return {"msg": "ok"}

    @app.get(
        "/login",
        dependencies=[Depends(rate_limit_dependency(f"{LOGIN_RATE_LIMIT}/min"))],
    )
    async def login():
        return {"msg": "login"}

    @app.get(
        "/custom",
        dependencies=[Depends(rate_limit_dependency(f"{CUSTOM_RATE_LIMIT}/min"))],
    )
    async def custom():
        return {"msg": "custom"}

    return app


# 1) Global middleware blocks after limit reached
@pytest.mark.asyncio
async def test_global_limit(app):
    app.state.limiter.storage = MemoryStorage()
    async with AsyncClient(app=app, base_url="http://test") as c:
        for _ in range(GLOBAL_RATE_LIMIT):
            assert (await c.get("/public")).status_code == 200

        r = await c.get("/public")
        assert r.status_code == 429


# 2) Per-route dependency overrides global limit
@pytest.mark.asyncio
async def test_dependency_limit(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        assert (await c.get("/login")).status_code == 200
        assert (await c.get("/login")).status_code == 200
        assert (await c.get("/login")).status_code == 429  # hit 2/min


# 3) IP-based identification works consistently
@pytest.mark.asyncio
async def test_ip_fallback(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/login")
        assert r.status_code == 200


# 4) Different routes have separate rate limits
@pytest.mark.asyncio
async def test_route_isolation(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        # exceed login limit
        await c.get("/login")
        await c.get("/login")
        assert (await c.get("/login")).status_code == 429
        # public route should still be allowed
        assert (await c.get("/public")).status_code == 200


# 5) Window resets properly when time passes
@pytest.mark.asyncio
async def test_window_resets(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        for _ in range(GLOBAL_RATE_LIMIT):
            await c.get("/public")
        assert (await c.get("/public")).status_code == 429

        # manually simulate window reset
        await asyncio.sleep(ALLOWED_TIME_FOR_WINDOW_RESET)
        # storage window shoud reset
        assert (await c.get("/public")).status_code == 200


# 6) Custom per-route rate works
@pytest.mark.asyncio
async def test_custom_route(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        for _ in range(CUSTOM_RATE_LIMIT):
            assert (await c.get("/custom")).status_code == 200
        assert (await c.get("/custom")).status_code == 429


# 7) Middleware does not conflict with dependency limiter
@pytest.mark.asyncio
async def test_global_plus_dependency_independent(app):
    async with AsyncClient(app=app, base_url="http://test") as c:

        for _ in range(LOGIN_RATE_LIMIT):
            await c.get("/login")
        assert (await c.get("/login")).status_code == 429

        # global should still allow 3 public routes
        assert (await c.get("/public")).status_code == 200


# 8) Storage increment_count works correctly
@pytest.mark.asyncio
async def test_storage_increments(app):
    storage = app.state.limiter.storage
    count1 = await storage.increment_count("testkey", 60)
    count2 = await storage.increment_count("testkey", 60)
    assert count1 == 1
    assert count2 == 2


# 9) Concurrency: multiple requests quickly should count correctly
@pytest.mark.asyncio
async def test_concurrent_requests(app):
    async with AsyncClient(app=app, base_url="http://test") as c:

        async def do_request():
            return await c.get("/public")

        tasks = [
            asyncio.create_task(do_request())
            for _ in range(GLOBAL_RATE_LIMIT + LOGIN_RATE_LIMIT)
        ]
        results = await asyncio.gather(*tasks)

        allowed = sum(1 for r in results if r.status_code == 200)
        blocked = sum(1 for r in results if r.status_code == 429)

        assert allowed == GLOBAL_RATE_LIMIT
        assert blocked == LOGIN_RATE_LIMIT
