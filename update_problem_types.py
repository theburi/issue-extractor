import yaml
import logging
import re
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict
from langchain_core.prompts import PromptTemplate 
from src.db.mongodb_client import connect_to_mongo, load_collection
from pymongo import MongoClient

from src.llm_utils import setup_llm

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB connection details
MONGO_URI = "your_mongo_uri"
DATABASE_NAME = "your_database_name"
COLLECTION_NAME = "processed_data"

# Problem types
PROBLEM_TYPES = [
    "Login Issues",
    "Billing Errors",
    "Delivery Delays",
    "Technical Support"
]

def load_configuration() -> Dict:
    config_path = Path("./config/config.yaml")
    config = []
    try:
        with open(config_path, 'r') as f:
            config= yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        raise

    try:
        with open(Path(config["paths"]["taxonomy"]), 'r') as f:
            config["taxonomy"] = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load taxonomy: {e}")
        raise
    logging.info("Configuration loaded successfully")
    return config

def analyze_description(description, template):
    """
    Analyze the description to determine the problem type using an LLM.
    
    Args:
        description (str): The description of the issue.
    
    Returns:
        str: The determined problem type.
    """
    # Setup LLM and embeddings        
    llm = setup_llm(config)
    prompt = PromptTemplate(
        template=template,
        input_variables=["text", "problem_types"]
        )
    chain = prompt | llm
    result = chain.invoke({
        "text": description,
        "problem_types": PROBLEM_TYPES
    })
    if ':' in result:
        result = result.split(':', 1)[1].strip()
    result = result.replace("'", "").replace('"', '')
    print(result)
    return result

def update_problem_types(config):
    
    # Connect to MongoDB
    db = connect_to_mongo(config["mongodb"]["uri"], config["mongodb"]["database"])
    records = load_collection(db, config["mongodb"]["processed_collection"])
    
    for description in records["description"].tolist():
        new_problem_type = analyze_description(description, config["prompts"]["problem_type"])
    
        # keep new issue types in a list and update taxonomy.yaml with new issue types
        new_problem_type = new_problem_type.strip()
        if new_problem_type.lower() not in [ptype.lower() for ptype in config["taxonomy"]["problem_types"]]:
            new_problem_type = new_problem_type.split('\n', 1)[0].strip().lower()
            cleaned_text = re.sub(r"[.\[\]\']", "", new_problem_type)

            if cleaned_text not in config["taxonomy"]["problem_types"]:
                config["taxonomy"]["problem_types"].append(cleaned_text)

                with open(config["paths"]["taxonomy"], 'w') as f:
                    yaml.dump(config["taxonomy"], f)
                    logging.info(f"New problem type added: {cleaned_text}")
                    config=load_configuration()


    logging.info("Problem type update completed.")

if __name__ == "__main__":
    load_dotenv()
    # Load configuration
    config = load_configuration()
    
    update_problem_types(config)
