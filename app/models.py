from pydantic import BaseModel
from typing import Optional, List

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = []

class CreateItemResponse(BaseModel):
    item_id: int
    item: Item
    message: str

class GetItemsResponse(BaseModel):
    items: List[Item]
    count: int


if __name__ == "__main__":
    # Example usage
    item = Item(name="Sample Item", description="This is a sample item", price=10.99, tags=["sample", "item"])
    print(item.model_json_schema())
    Item.model_validate_json(r"""{"name": "Sample Item", "description": "This is a sample item", "price": 10.99, "tags": ["sample", "item"]}""")
