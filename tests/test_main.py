import pytest
from httpx import AsyncClient, ASGITransport # Import ASGITransport
from app.main import app, db # Import db to allow clearing for tests

# Fixture to clear the in-memory database before each test
@pytest.fixture(autouse=True)
def clear_db_before_each_test():
    db.clear()
    # Reset next_item_id if it's a global in main.py that needs resetting
    # For this example, we'll assume it's handled or tests are designed around it.
    # If next_item_id is also in app.main, you might need:
    # from app import main as main_app
    # main_app.next_item_id = 1
    # However, directly manipulating globals like this can be tricky.
    # A better approach for `next_item_id` might be to make it part of a class
    # or a more robust state management solution if tests need to reset it.
    # For now, clearing `db` is the primary concern for test isolation.
    # Let's assume `app.main.next_item_id` should be reset.
    # This requires `next_item_id` to be accessible for modification.
    # If `next_item_id` is defined in `app.main`, you'd do:
    import app.main
    app.main.next_item_id = 1


BASE_URL = "http://localhost:8000" # Standard base URL for in-process testing with app=app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_create_item_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        item_data = {
            "name": "Test Item 1",
            "description": "A test item",
            "price": 9.99,
            "tags": ["test", "example"]
        }
        response = await ac.post("/items/", json=item_data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["item"]["name"] == item_data["name"]
    assert response_json["message"] == "Item created successfully"
    assert "item_id" in response_json
    assert response_json["item_id"] == 1 # First item

@pytest.mark.asyncio
async def test_create_item_duplicate_name():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        item_data = {
            "name": "Unique Item Name For Duplicate Test",
            "description": "First instance",
            "price": 10.00
        }
        # Create the first item
        post_response1 = await ac.post("/items/", json=item_data)
        assert post_response1.status_code == 201, "Setup: Failed to create the first item"

        # Attempt to create another item with the same name
        duplicate_item_data = {
            "name": "Unique Item Name For Duplicate Test", # Same name
            "description": "Second instance, should fail",
            "price": 20.00
        }
        response = await ac.post("/items/", json=duplicate_item_data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Item with name 'Unique Item Name For Duplicate Test' already exists"

@pytest.mark.asyncio
async def test_get_items_empty_initially():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        response = await ac.get("/items/")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["items"] == []
    assert response_json["count"] == 0

@pytest.mark.asyncio
async def test_get_items_after_creation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        item1_data = {"name": "Item A", "price": 1.0}
        item2_data = {"name": "Item B", "price": 2.0}
        
        await ac.post("/items/", json=item1_data)
        await ac.post("/items/", json=item2_data)
        
        response = await ac.get("/items/")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["count"] == 2
    item_names = {item["name"] for item in response_json["items"]}
    assert "Item A" in item_names
    assert "Item B" in item_names

@pytest.mark.asyncio
async def test_get_specific_item_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        item_data = {
            "name": "Specific Item Test",
            "description": "Details for specific item",
            "price": 12.34,
            "tags": ["specific"]
        }
        post_response = await ac.post("/items/", json=item_data)
        assert post_response.status_code == 201
        item_id = post_response.json()["item_id"]

        response = await ac.get(f"/items/{item_id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == item_data["name"]
    assert response_json["price"] == item_data["price"]

@pytest.mark.asyncio
async def test_get_specific_item_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        non_existent_id = 99999 # Assuming this ID won't exist after db clear
        response = await ac.get(f"/items/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
