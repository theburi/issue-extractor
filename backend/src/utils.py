import logging
import yaml
from pathlib import Path
from typing import List, Dict
from src.db.mongodb_client import connect_to_mongo

def load_configuration(project_id=None) -> Dict:
    config_path = Path("./config/config.yaml")
    config = []
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
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

    try:
        # Check if project_id is provided
        if project_id:            
            logging.info(f"Fetching configuration overrides for project_id: {project_id}")
            # Connect to MongoDB
            db = connect_to_mongo(
                config["mongodb"]["uri"], config["mongodb"]["database"])
            project = db[config["mongodb"]["projects_collection"]].find_one({'_id': project_id})
            
            if project:
                # Override jira_source and prompts if they exist in the project document
                if 'jira_source' in project:
                    logging.info(f"Overriding jira_source from project: {project_id}")
                    config['issue-extractor']['jira_source'] = project['jira_source']
                
                if 'prompts' in project:
                    logging.info(f"Overriding prompts from project: {project_id}")
                    config['prompts'] = project['prompts']
            else:
                logging.warning(f"No project found with project_id: {project_id}")
    except Exception as e:
        logging.error(f"Error fetching project configuration: {str(e)}")

    return config