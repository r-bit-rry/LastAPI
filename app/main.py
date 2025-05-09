from fastapi import FastAPI, HTTPException
from typing import List, Dict
from app.models import Item, CreateItemResponse, GetItemsResponse

app = FastAPI(
    title="InterviewAPI",
    description="A simple web service for an interview, demonstrating FastAPI capabilities.",
    version="0.1.0"
)

# In-memory "database"
db: Dict[int, Item] = {}
next_item_id = 1

@app.post("/items/", response_model=CreateItemResponse, status_code=201)
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
        raise HTTPException(status_code=400, detail=f"Item with name '{item.name}' already exists")
    
    db[next_item_id] = item
    response = CreateItemResponse(item_id=next_item_id, item=item, message="Item created successfully")
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
