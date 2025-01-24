from flask import Blueprint, request, jsonify
import logging
import os
import re
from src.utils import load_configuration
from src.db.mongodb_client import connect_to_mongo
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
config = load_configuration()

# Get Jira token from environment variables
jira_token = os.getenv('JIRA_TOKEN')
if not jira_token:
    raise EnvironmentError('JIRA_TOKEN environment variable is not set.')

# Create a Blueprint for the issues API
feature_bp = Blueprint('feature_request', __name__)

# Connect to MongoDB
db = connect_to_mongo(
    config["mongodb"]["uri"], config["mongodb"]["database"])
collection = db[config["mongodb"]["raw_collection"]]  # Replace with your collection name

def process_issue(issue):
    try:
        
        # Extract comments as a list of dictionaries
        comments = [
            {
                "author": comment.author.displayName if hasattr(comment, "author") else None,
                "body": re.sub(r"\[~[^\]]+\]", "[email]", comment.body),
                "created": comment.created if hasattr(comment, "created") else None,
            }
            for comment in getattr(issue.fields.comment, 'comments', [])
        ]
        full_description = f"{issue.fields.description}\n\nComments:\n" + "\n".join(
            [f"Comment {idx + 1}: {c['body']}" for idx, c in enumerate(comments)]
        ) if issue.fields.description else "No Description\n\nComments:\n" + "\n".join(
            [f"Comment {idx + 1}: {c['body']}" for idx, c in enumerate(comments)]
        )
        full_description = full_description.replace("\r\n", "\n")
        full_description = full_description.replace("\n\n", "\n")


        return {
            'key': issue.key,
            'summary': issue.fields.summary,
            'description': issue.fields.description,
            'description_llm': full_description,
            'status': issue.fields.status.name,
            'created_date': issue.fields.created,
            'updated_date': issue.fields.updated,
            'components': [component.name for component in issue.fields.components],
            'type': issue.fields.issuetype.name,
            'priority': issue.fields.priority.name if issue.fields.priority else None,
            'labels': issue.fields.labels if issue.fields.labels else [],
            'cid': getattr(issue.fields, 'customfield_11212', None),
            'comments': comments
        }
    except AttributeError as e:
        logging.warning(f"Error extracting data from issue {issue.key}: {e}")
        return None

@feature_bp.route('/api/feature-request', methods=['GET'])
def get_issue():
    jira_key = request.args.get('jira_key')
    # Connect to Jira with error handling
    try:
        jira = JIRA(server='https://jira.camunda.com/', token_auth=jira_token)
        logging.info("Successfully connected to Jira.")
        issue = jira.search_issues(f'key={jira_key}')        
        if not issue:
            logging.error(f"Failed to find issue with key {jira_key}")
            return {"error": f"Failed to find issue with key {jira_key}"}, 404
        return {"data": process_issue(issue[0]) }, 200
    except Exception as e:
        logging.error(f"Failed to connect to Jira: {e}")
        raise

