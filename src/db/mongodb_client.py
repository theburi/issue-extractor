from pymongo import MongoClient
import pandas as pd

def connect_to_mongo(uri: str, database: str):
    """Establish a connection to MongoDB."""
    client = MongoClient(uri)
    return client[database]

def load_collection(db, collection_name: str) -> pd.DataFrame:
    """Loads data from a MongoDB collection into a DataFrame."""
    collection = db[collection_name]
    data = list(collection.find())
    return pd.DataFrame(data)

def insert_to_collection(db, collection_name: str, data: pd.DataFrame):
    """Inserts a DataFrame into a MongoDB collection."""
    collection = db[collection_name]
    collection.insert_many(data.to_dict("records"))
