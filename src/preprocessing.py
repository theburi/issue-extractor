import pandas as pd
import re
import logging
from datetime import datetime
from src.db.mongodb_client import load_collection, insert_to_collection

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_data_from_mongo(db, collection_name: str) -> pd.DataFrame:
    """
    Fetches raw customer communication data from MongoDB.
    
    Args:
        db: MongoDB database connection.
        collection_name (str): Name of the collection to fetch data from.
    
    Returns:
        pd.DataFrame: DataFrame containing the raw data.
    """
    logging.info(f"Loading data from collection: {collection_name}")
    return load_collection(db, collection_name)


def clean_text(text: str) -> str:
    """
    Cleans a single text entry by removing unnecessary characters, whitespace, and noise.
    
    Args:
        text (str): Raw text data.
    
    Returns:
        str: Cleaned text.
    """
    if not isinstance(text, str):
        return None
    
    text = text.lower()  # Convert to lowercase
    text = re.sub(r"http\S+|www\S+", "", text)  # Remove URLs
    text = re.sub(r"\s+", " ", text)  # Replace multiple whitespaces with a single space
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove special characters
    
    cleaned_text = text.strip()  # Remove leading/trailing whitespace
    
    # Return None if the cleaned text is empty or only whitespace
    return cleaned_text if cleaned_text else None


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw customer communication data.
    
    Args:
        data (pd.DataFrame): Raw data with at least 'description' column.
    
    Returns:
        pd.DataFrame: Cleaned data.
    """
    if "description" not in data.columns:
        raise ValueError("DataFrame must contain a 'description' column", data.columns)
    
    logging.info(f"Starting data cleaning process. {len(data)}")
    data["description"] = data["description"].apply(clean_text)
    data.dropna(subset=["description"], inplace=True)  # Remove rows with empty communication
    data.reset_index(drop=True, inplace=True)
    logging.info("Data cleaning process completed.")
    return data


def add_metadata(data: pd.DataFrame) -> pd.DataFrame:
    """
    Adds metadata such as timestamp and unique IDs to the data.
    
    Args:
        data (pd.DataFrame): Cleaned customer data.
    
    Returns:
        pd.DataFrame: Data with metadata added.
    """
    logging.info("Adding metadata to the data.")
    data["processed_at"] = datetime.utcnow()
    if "customer_id" not in data.columns:
        data["customer_id"] = range(1, len(data) + 1)
    return data


def save_processed_data_to_mongo(db, collection_name: str, data: pd.DataFrame):
    """
    Saves the cleaned and processed data back to MongoDB.
    
    Args:
        db: MongoDB database connection.
        collection_name (str): Collection to save processed data into.
        data (pd.DataFrame): Cleaned and processed data.
    """
    logging.info(f"Saving processed data to collection: {collection_name}")
    insert_to_collection(db, collection_name, data)
    logging.info("Processed data successfully saved to MongoDB.")
