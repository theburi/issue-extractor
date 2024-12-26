import logging
from typing import List
import openai
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set your OpenAI API key (or use a configuration manager)
openai.api_key = "your_openai_api_key"

def summarize_text(text: str, model: str = "gpt-3.5-turbo", max_tokens: int = 150) -> str:
    """
    Generates a summary for a single communication using OpenAI's GPT model.
    
    Args:
        text (str): The input text to summarize.
        model (str): The GPT model to use (default: "gpt-3.5-turbo").
        max_tokens (int): Maximum number of tokens in the summary.
    
    Returns:
        str: The summary of the input text.
    """
    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        return ""

    try:
        logging.info("Generating summary for a single text.")
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes customer feedback."},
                {"role": "user", "content": text},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        summary = response["choices"][0]["message"]["content"].strip()
        logging.info("Summary generated successfully.")
        return summary
    except Exception as e:
        logging.error(f"Error in summarizing text: {e}")
        return "Error in generating summary."


def batch_summarize(data: pd.DataFrame, text_column: str = "communication", model: str = "gpt-3.5-turbo") -> pd.DataFrame:
    """
    Summarizes customer communications in a batch process.
    
    Args:
        data (pd.DataFrame): DataFrame containing customer communications.
        text_column (str): The column name containing the text to summarize.
        model (str): The GPT model to use for summarization.
    
    Returns:
        pd.DataFrame: DataFrame with an additional column for summaries.
    """
    if text_column not in data.columns:
        raise ValueError(f"The specified text column '{text_column}' is not in the DataFrame.")

    logging.info("Starting batch summarization process.")
    data["summary"] = data[text_column].apply(lambda x: summarize_text(x, model=model))
    logging.info("Batch summarization completed.")
    return data


def save_summaries_to_mongo(db, collection_name: str, data: pd.DataFrame):
    """
    Saves summarized data back to MongoDB.
    
    Args:
        db: MongoDB database connection.
        collection_name (str): Collection to save summarized data into.
        data (pd.DataFrame): Data with summaries added.
    """
    from src.db.mongodb_client import insert_to_collection
    logging.info(f"Saving summarized data to collection: {collection_name}")
    insert_to_collection(db, collection_name, data)
    logging.info("Summarized data successfully saved to MongoDB.")
