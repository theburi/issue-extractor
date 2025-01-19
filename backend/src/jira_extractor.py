import os
import pandas as pd
import re
from bson import ObjectId 
from jira import JIRA
import logging
from dotenv import load_dotenv
import time
from pymongo import MongoClient
from src.utils import load_configuration

CUSTOMER_CIDS = []  # List of customer IDs

# Load environment variables
load_dotenv()

# Setup logging with more detail
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MongoDB Connection Setup
mongo_client = MongoClient('localhost', 27017)  # Update host and port if needed
db = mongo_client['jira_data']  # Replace 'jira_data' with your database name
collection = db['issues']  # Replace 'issues' with your collection name

# Get Jira token from environment variables
jira_token = os.getenv('JIRA_TOKEN')
if not jira_token:
    raise EnvironmentError('JIRA_TOKEN environment variable is not set.')

# Connect to Jira with error handling
try:
    jira = JIRA(server='https://jira.camunda.com/', token_auth=jira_token)
    logging.info("Successfully connected to Jira.")
except Exception as e:
    logging.error(f"Failed to connect to Jira: {e}")
    raise

def extract_issue_data(issue):
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
            'description': full_description,
            'status': issue.fields.status.name,
            'created_date': issue.fields.created,
            'updated_date': issue.fields.updated,
            'components': [component.name for component in issue.fields.components],
            'type': issue.fields.issuetype.name,
            'priority': issue.fields.priority.name if issue.fields.priority else None,
            'labels': issue.fields.labels if issue.fields.labels else [],
            'cid': getattr(issue.fields, 'customfield_11212', None),
            'comments': comments,

        }
    except AttributeError as e:
        logging.warning(f"Error extracting data from issue {issue.key}: {e}")
        return None

def extract_issues(jql_query, start_at=0, max_results=100):
    data = []

    while True:
        try:
            issues = jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
            if not issues:
                break

            for issue in issues:
                issue_data = extract_issue_data(issue)
                issue_data['jira_source'] = jql_query
                if issue_data:
                    data.append(issue_data)
            
            logging.info(f"Extracted {len(issues)} issues from Jira, starting at {start_at}.")
            start_at += max_results
            time.sleep(1)  # Sleep to handle rate limiting

        except Exception as e:
            logging.error(f"Error extracting issues at start {start_at}: {e}")
            break

    df = pd.DataFrame(data)    
    return df

def main_execution_flow(project_id):
    # Load configuration
    config = load_configuration()
    
    # Fetch the jira_source from the projects collection
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        logging.error(f"Project with ID {project_id} not found.")
        return
    
    jql_query = project.get('jira_source')
    if not jql_query:
        logging.error(f"Jira source query not found for project ID {project_id}.")
        return

    issues_df = extract_issues(jql_query)  
    if not issues_df.empty:
        for _, issue in issues_df.iterrows():
            # Convert issue data to a dictionary
            issue_data = issue.to_dict()
            issue_data["project_id"] = project_id

            # Upsert each issue into MongoDB
            collection.update_one(
                {'key': issue_data['key'], issue_data["project_id"]: project_id},  # Match issue by key
                {'$set': issue_data},  # Update fields with new data
                upsert=True  # Insert if it doesn't exist
            )
        logging.info(f"Upserted {len(issues_df)} issues into MongoDB for project ID: {project_id}.")
    else:
        logging.info(f"No issues found for project ID: {project_id}.")
    return { "issues_count":len(issues_df), "project_id": project_id }

if __name__ == "__main__":
    cid = ''
    main_execution_flow(cid)