import logging
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Callable
from app.models import Item, CreateItemResponse, GetItemsResponse
from fastapi import Depends
import hashlib
import json
import asyncio

try:
    from fastapi_limiter import FastAPILimiter
    from fastapi_limiter.depends import RateLimiter
    import redis.asyncio as redis_asyncio

    _has_limiter = True
except ImportError:
    _has_limiter = False


# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("InterviewAPI")

app = FastAPI(
    title="InterviewAPI",
    description="A simple web service for an interview, demonstrating FastAPI capabilities.",
    version="0.1.0",
)


# --- No-op OAuth2 Authentication Middleware Stub ---
# @app.middleware("http")
# async def oauth2_auth_stub(request: Request, call_next: Callable):
#     """
#     No-op OAuth2 authentication middleware stub.

#     This does NOT perform any real authentication. To implement real OAuth2 authentication:
#     1. Use `fastapi.security.OAuth2PasswordBearer` for token extraction.
#     2. Validate the token (e.g., with a JWT library or an OAuth2 provider).
#     3. Attach user info to the request (e.g., request.state.user).
#     4. Raise HTTPException(401) on invalid/missing tokens.
#     See FastAPI docs: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
#     """
#     # Example: token = request.headers.get("Authorization")
#     response = await call_next(request)
#     return response


# --- Smart Redis Caching Middleware with In-Memory Sync ---
redis_cache = {}
REDIS_CHANNEL = "db_events"

def make_cache_key(request: Request) -> str:
    """Create a smart cache key based on method, path, and sorted query params/body."""
    key_data = {
        "method": request.method,
        "url": str(request.url.path),
        "query": tuple(sorted(request.query_params.items())),
    }
    # For POST/PUT, include the body
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = asyncio.run(request.body())
            key_data["body"] = body.decode("utf-8")
        except Exception:
            pass
    raw = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()

@app.middleware("http")
async def redis_cache_middleware(request: Request, call_next: Callable):
    if not _has_limiter:
        return await call_next(request)
    cache_key = make_cache_key(request)
    # Try in-memory cache first
    if cache_key in redis_cache:
        logger.info(f"Cache hit (memory) for {request.method} {request.url}")
        return JSONResponse(content=redis_cache[cache_key]["data"], status_code=redis_cache[cache_key]["status_code"])
    # Try Redis
    redis_cli = redis_asyncio.from_url("redis://localhost:6379/0", encoding="utf8", decode_responses=True)
    cached = await redis_cli.get(cache_key)
    if cached:
        logger.info(f"Cache hit (redis) for {request.method} {request.url}")
        cached_data = json.loads(cached)
        redis_cache[cache_key] = cached_data
        return JSONResponse(content=cached_data["data"], status_code=cached_data["status_code"])
    # Cache miss: process request
    response = await call_next(request)
    # Only cache GET/HEAD/OPTIONS responses
    if request.method in ("GET", "HEAD", "OPTIONS") and response.status_code == 200:
        resp_body = b""
        async for chunk in response.body_iterator:
            resp_body += chunk
        try:
            data = json.loads(resp_body.decode())
        except Exception:
            data = resp_body.decode()
        cache_entry = {"data": data, "status_code": response.status_code}
        redis_cache[cache_key] = cache_entry
        await redis_cli.set(cache_key, json.dumps(cache_entry), ex=60)  # 1 min expiry
    return response

# --- Redis Pub/Sub: Sync in-memory cache with Redis events ---
async def redis_subscriber():
    if not _has_limiter:
        return
    redis_cli = redis_asyncio.from_url("redis://localhost:6379/0", encoding="utf8", decode_responses=True)
    pubsub = redis_cli.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)
    logger.info("Subscribed to Redis channel for cache events")
    async for message in pubsub.listen():
        if message["type"] == "message":
            event = json.loads(message["data"])
            action = event.get("action")
            key = event.get("key")
            if action == "evict" and key in redis_cache:
                redis_cache.pop(key, None)
                logger.info(f"Evicted in-memory cache for key: {key}")
            elif action == "add" and key:
                redis_cache[key] = event.get("value")
                logger.info(f"Added/updated in-memory cache for key: {key}")

@app.on_event("startup")
async def start_redis_subscriber():
    if _has_limiter:
        asyncio.create_task(redis_subscriber())


@app.on_event("startup")
async def startup_event():
    if _has_limiter:
        redis_url = "redis://localhost:6379/0"  # Change in production
        await FastAPILimiter.init(
            redis_asyncio.from_url(redis_url, encoding="utf8", decode_responses=True)
        )
        logger.info("fastapi-limiter initialized with Redis at %s", redis_url)
    else:
        logger.warning(
            "fastapi-limiter or redis is not installed. Rate limiting is disabled."
        )

# In-memory "database"
db: Dict[int, Item] = {}
next_item_id = 1


@app.post(
    "/items/",
    response_model=CreateItemResponse,
    status_code=201,
    dependencies=[Depends(RateLimiter(times=2, seconds=10))] if _has_limiter else [],
)
async def create_item(item: Item):
    """
    Create a new item and store it in the in-memory database.

    This endpoint receives an `Item` object in the request body,
    validates it using the Pydantic model, and if an item with the
    same name doesn't already exist, it assigns a new ID to it,
    stores it, and returns the created item along with its ID and a success message.

    Args:
        item (Item): The item to create. Expected to match the `Item` Pydantic model,
                     containing fields like `name`, `description`, `price`, and `tags`.

    Returns:
        CreateItemResponse: A Pydantic model containing the `item_id` of the newly created item,
                            the `item` data itself, and a confirmation `message`.

    Raises:
        HTTPException: 400 error if an item with the same name already exists.
    """
    global next_item_id
    # Check for duplicate item names before adding
    if any(existing_item.name == item.name for existing_item in db.values()):
        raise HTTPException(
            status_code=400, detail=f"Item with name '{item.name}' already exists"
        )

    db[next_item_id] = item
    response = CreateItemResponse(
        item_id=next_item_id, item=item, message="Item created successfully"
    )
    next_item_id += 1
    return response


@app.get("/items/", response_model=GetItemsResponse)
async def get_items():
    """
    Retrieve a list of all items currently stored in the in-memory database.

    This endpoint returns all items that have been created via the POST `/items/`
    endpoint. The response includes a list of item objects and a count of the total
    number of items.

    Returns:
        GetItemsResponse: A Pydantic model containing a list of `items` and the `count`
                          of items.
    """
    return GetItemsResponse(items=list(db.values()), count=len(db))


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """
    Retrieve a specific item by its unique ID.

    This endpoint takes an integer `item_id` as a path parameter and returns
    the corresponding item if found.

    Args:
        item_id (int): The unique identifier of the item to retrieve. This is passed
                       as a path parameter.

    Returns:
        Item: The Pydantic model representing the requested item.

    Raises:
        HTTPException: 404 error if an item with the specified `item_id` is not found.
    """
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    A simple health check endpoint.

    This endpoint can be used to verify that the API server is running and responsive.
    It returns a simple JSON object indicating the status.

    Returns:
        dict: A dictionary with a "status" key and "ok" value, e.g., `{"status": "ok"}`.
    """
    return {"status": "ok"}


# --- Custom Exception Handler Middleware ---
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    """
    Custom exception handler for all unhandled exceptions.
    Logs the error and returns a generic JSON error message.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support."},
    )


# --- CORS Middleware Example (optional, but common) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
