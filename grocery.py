from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from bson import ObjectId
import os

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "grocery_manager"
COLLECTION_NAME = "grocery_lists"

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
grocery_collection = db[COLLECTION_NAME]

# FastAPI app initialization
app = FastAPI()

# Pydantic models for request and response validation
class GroceryItem(BaseModel):
    name: str
    quantity: int
    purchased: bool = False

class GroceryList(BaseModel):
    title: str
    items: List[GroceryItem]

# Utility to convert ObjectId to string
def object_id_to_str(item):
    item["_id"] = str(item["_id"])
    return item

# API Endpoints

@app.post("/grocery-lists/", response_model=dict)
async def create_grocery_list(grocery_list: GroceryList):
    """
    Create a new grocery list.
    """
    list_dict = grocery_list.dict()
    result = grocery_collection.insert_one(list_dict)
    return {"message": "Grocery list created successfully", "id": str(result.inserted_id)}

@app.get("/grocery-lists/", response_model=List[dict])
async def get_all_grocery_lists():
    """
    Retrieve all grocery lists.
    """
    lists = list(grocery_collection.find())
    return [object_id_to_str(grocery_list) for grocery_list in lists]

@app.get("/grocery-lists/{list_id}", response_model=dict)
async def get_grocery_list(list_id: str):
    """
    Retrieve a single grocery list by ID.
    """
    grocery_list = grocery_collection.find_one({"_id": ObjectId(list_id)})
    if not grocery_list:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return object_id_to_str(grocery_list)

@app.put("/grocery-lists/{list_id}", response_model=dict)
async def update_grocery_list(list_id: str, updated_list: GroceryList):
    """
    Update a grocery list by ID.
    """
    result = grocery_collection.update_one(
        {"_id": ObjectId(list_id)},
        {"$set": updated_list.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return {"message": "Grocery list updated successfully"}

@app.delete("/grocery-lists/{list_id}", response_model=dict)
async def delete_grocery_list(list_id: str):
    """
    Delete a grocery list by ID.
    """
    result = grocery_collection.delete_one({"_id": ObjectId(list_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return {"message": "Grocery list deleted successfully"}

@app.post("/grocery-lists/{list_id}/items", response_model=dict)
async def add_item_to_grocery_list(list_id: str, item: GroceryItem):
    """
    Add an item to an existing grocery list.
    """
    result = grocery_collection.update_one(
        {"_id": ObjectId(list_id)},
        {"$push": {"items": item.dict()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return {"message": "Item added to grocery list"}

@app.put("/grocery-lists/{list_id}/items/{item_name}", response_model=dict)
async def update_item_status(list_id: str, item_name: str, purchased: bool):
    """
    Update the purchased status of an item in a grocery list.
    """
    result = grocery_collection.update_one(
        {"_id": ObjectId(list_id), "items.name": item_name},
        {"$set": {"items.$.purchased": purchased}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grocery list or item not found")
    return {"message": "Item status updated"}

@app.delete("/grocery-lists/{list_id}/items/{item_name}", response_model=dict)
async def delete_item_from_grocery_list(list_id: str, item_name: str):
    """
    Delete an item from a grocery list.
    """
    result = grocery_collection.update_one(
        {"_id": ObjectId(list_id)},
        {"$pull": {"items": {"name": item_name}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Grocery list or item not found")
    return {"message": "Item deleted from grocery list"}
