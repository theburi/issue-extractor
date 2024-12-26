import pytest
from src.db.mongodb_client import connect_to_mongo, load_collection

def test_mongo_connection():
    db = connect_to_mongo("mongodb://localhost:27017", "test_db")
    assert db.name == "test_db"

def test_load_collection():
    db = connect_to_mongo("mongodb://localhost:27017", "test_db")
    data = load_collection(db, "test_collection")
    assert isinstance(data, pd.DataFrame)
