from src.llm_utils import parse_llm_output, setup_llm
from langchain_core.prompts import PromptTemplate 
from collections import Counter
import logging
import shutil
from pathlib import Path
from typing import List, Dict
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
from src.db.mongodb_client import connect_to_mongo, load_collection, insert_to_collection
from src.preprocessing import clean_data
from src.problem_extraction import standardize_problems
from src.reporting import generate_enhanced_report, generate_problem_report
from src.llm_utils import parse_llm_output, setup_llm, setup_embeddings
from src.utils import load_configuration
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def analyze_description_problem_type(description, taxonomy, config):
    """
    Analyze the issue to determine its problem type using an LLM.
    
    Args:
        description (str): The description of the issue.
        taxonomy (dict): Taxonomy of problem types.
    
    Returns:
        dict: {
            "confidence": int,
            "problem_type": str,
            "problem_type_description": str
        }
    """

    try:
        llm = setup_llm(config)
        prompt = PromptTemplate(
            template=config["prompts"]["problem_type_classification"],
            input_variables=["description", "taxonomy"]
        )
        chain = prompt | llm

        results = chain.invoke({
            "description":description,
            "taxonomy": taxonomy
        })
        parsed_output = results

        if not parsed_output or "problem_type" not in parsed_output[0]:
            raise ValueError("Failed to parse LLM response.")

        problem_type_data = parsed_output[0]
        problem_type = problem_type_data.get("problem_type", "unknown")
        confidence = int(problem_type_data.get("confidence", 0))
        problem_type_description = taxonomy["problem_descriptions"].get(problem_type, "No description available.")

        return {
            "confidence": confidence,
            "problem_type": problem_type,
            "problem_type_description": problem_type_description
        }

    except Exception as e:
        logging.error(f"Error analyzing problem type: {e}", exc_info=True)
        return {
            "confidence": 0,
            "problem_type": "unknown",
            "problem_type_description": "Unable to determine problem type."
        }


def problem_frequency_analysis(data: pd.DataFrame) -> pd.DataFrame:
    """
    Counts the frequency of each problem across the dataset.
    
    Args:
        data (pd.DataFrame): Processed data with a 'problems' column.
    
    Returns:
        pd.DataFrame: DataFrame with problems and their frequencies.
    """
    print (data.columns)
    if "problem_type" not in data.columns:
        raise ValueError("DataFrame must contain a 'problem_type' column")
    
    logging.info("Starting problem frequency analysis.")
    frequency_df =  (
        data
        .groupby(["cluster_id", "problem_type"], as_index=False)["frequency"]
        .sum()
    )
    frequency_df.sort_values(by=["cluster_id", "frequency"], ascending=False, inplace=True)
    logging.info("Problem frequency analysis completed.")
    return frequency_df

def analyze_problem_trends(data: pd.DataFrame, date_column: str = "processed_at") -> pd.DataFrame:
    """
    Analyzes problem trends over time.
    
    Args:
        data (pd.DataFrame): Processed data with 'problems' and a date column.
        date_column (str): The name of the column containing timestamps.
    
    Returns:
        pd.DataFrame: A DataFrame showing the number of occurrences of each problem over time.
    """
    if date_column not in data.columns or "problems" not in data.columns:
        raise ValueError(f"DataFrame must contain '{date_column}' and 'problems' columns")
    
    logging.info("Analyzing problem trends over time.")
    data[date_column] = pd.to_datetime(data[date_column])
    data["date"] = data[date_column].dt.date
    exploded_data = data.explode("problems")
    trends = exploded_data.groupby(["date", "problems"]).size().reset_index(name="frequency")
    logging.info("Problem trend analysis completed.")
    return trends

def generate_cluster_summary(clustered_problems: Dict[int, List[Dict[str, str]]], llm, config) -> Dict[int, str]:
    """
    Generate concise summaries for each cluster using LangChain.

    Args:
        clustered_problems (Dict[int, List[Dict[str, str]]]): Clustered problems data.
        llm (OpenAI): LangChain LLM instance.

    Returns:
        Dict[int, str]: A dictionary where keys are cluster IDs and values are summaries.
    """
    logging.info("Generating summaries for each cluster.")
    summaries = pd.DataFrame(columns=["cluster_id", "keys", "summary"])
    llm = setup_llm(config, max_tokens=200)

    for cluster_id, problems in clustered_problems.items():
        descriptions = "\n".join([problem["description"] for problem in problems])
        print("Number of problems in cluster", cluster_id, ":", len(problems))
        summary={}
        summary["cluster_id"] = cluster_id
        summary["keys"] = [
            problem["key"] for problem in problems
        ]
        try:
            prompt = PromptTemplate(
                template=config["prompts"]["generate_cluster_summary"],
                input_variables=["descriptions"]
                )
            chain = prompt | llm
            results = chain.invoke({
                "descriptions": descriptions
                })
            summary["summary"] = results.strip()

            logging.info(f"Summary for cluster {cluster_id}:")
            
        except Exception as e:
            logging.error(f"Failed to generate summary for cluster {cluster_id}: {e}")
            summary["summary"] = "Error in generating summary."
        summaries.loc[len(summaries)] = summary

    logging.info("Cluster summaries generated successfully.")
    return summaries


def create_vector_store(documents: List, embeddings) -> Chroma:
    # Convert each string document into a Document object
    document_objects = [Document(page_content=doc) for doc in documents]

    """Create and populate vector store."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(document_objects)

    # Ensure the vector store directory is empty before creating a new one. Delete it.
    persist_directory = Path("./data/vectorstore")
    if persist_directory.exists():
        logging.info("Removing existing vector store and its contents.")
        shutil.rmtree(persist_directory)

    return Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=str(persist_directory)
    )


def assess_optimal_n_clusters(embeddings: List[np.ndarray], max_clusters: int = 10) -> int:
    """
    Assess the optimal number of clusters using the silhouette score.

    Args:
        embeddings (List[np.ndarray]): List of semantic embeddings for problems.
        max_clusters (int): Maximum number of clusters to evaluate.

    Returns:
        int: Optimal number of clusters.
    """
    logging.info("Assessing the optimal number of clusters.")
    best_n_clusters = 2
    best_score = -1

    for n_clusters in range(2, max_clusters + 1):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, cluster_labels)
        logging.info(f"Silhouette score for {n_clusters} clusters: {score}")

        if score > best_score:
            best_n_clusters = n_clusters
            best_score = score

    logging.info(f"Optimal number of clusters: {
                 best_n_clusters} with silhouette score: {best_score}")
    return best_n_clusters


def semantic_clustering(
    problem_rows: List[Dict[str, str]],
    embeddings: List[np.ndarray],
    n_clusters: int = 5,
    outlier_threshold: float = 2.0
) -> Dict[int, List[Dict[str, str]]]:
    
    """Cluster problems based on their semantic embeddings."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)

    # Calculate distances to cluster centers
    _, distances = pairwise_distances_argmin_min(
        embeddings, kmeans.cluster_centers_)

    # Create a dictionary for each cluster
    clustered_problems = {i: [] for i in range(n_clusters)}

    # Assign problems to clusters if within the outlier threshold
    for row, cluster_id, distance in zip(problem_rows, clusters, distances):
        if distance <= outlier_threshold:
            clustered_problems[cluster_id].append(row)
        else:
            logging.warning(f"Excluding outlier: {
                            row['description']} (distance: {distance})")

    # 'clusters' aligns with 'problem_rows' index by index
    for row, cluster_id in zip(problem_rows, clusters):
        # Append the entire row dict, which includes description + problem_type
        clustered_problems[cluster_id].append(row)

    return clustered_problems


def preprocess_clustered_problems(
    clustered_problems: Dict[int, List[Dict[str, str]]]
) -> pd.DataFrame:
    """
    Preprocess clustered problems into a DataFrame with counts 
    (based on problem_type rather than raw description).
    """
    processed_data = []

    for cluster_id, rows in clustered_problems.items():
        # Extract the 'problem_type' for each row in the cluster
        problem_types = [row["problem_type"] for row in rows]

        # Count how many times each problem_type appears
        problem_type_counts = pd.Series(problem_types).value_counts().to_dict()

        for p_type, count in problem_type_counts.items():
            processed_data.append({
                "cluster_id": cluster_id,
                "problem_type": p_type,
                "frequency": count
            })

    return pd.DataFrame(processed_data)


def process_row(row, vector_store, llm, taxonomy, config, db, projectId):
    """Process a single row of data."""
    try:
        # Check if the record already exists

        existing_record = db[config["mongodb"]["processed_collection"]].find_one(
            {
                "key": row["key"], 
                "version": config["prompts"]["version"], 
                "project_id": projectId
            }
        )
        if existing_record:
            logging.info(f"Record with key {row['key']} and version {
                         config['prompts']['version']} already exists. Skipping processing.")
            return []

        similar_docs = vector_store.similarity_search(row['description'], k=3)
        similar_cases = "\n".join([d.page_content for d in similar_docs])

        prompt = PromptTemplate(
            template=config["prompts"]["problem_extraction"],
            input_variables=["text", "similar_cases"]
        )
        chain = prompt | llm
        results = chain.invoke({
            "text": row['description'],
            "similar_cases": similar_cases
        })
        standardized_results = [standardize_problems(
            result, taxonomy) for result in parse_llm_output(results)]
        for result in standardized_results:
            result["customer_id"] = row["cid"]
            result["key"] = row["key"]
            result["version"] = config["prompts"]["version"]
        return standardized_results
    except Exception as e:
        logging.error(f"Error processing row: {e}", exc_info=True)
        return []


def process_and_store_problems(cleaned_data, vector_store, llm, config, db, projectId):
    standardized_problems = []
    for _, row in cleaned_data.iterrows():
        if 'key' not in row:
            logging.error(f"Missing 'key' in row: {row}")
            continue
        problems = process_row(row, vector_store, llm,
                               config["taxonomy"], config, db, projectId)
        for problem in problems:
            standardized_problems.extend(problem)
            db[config["mongodb"]["processed_collection"]].update_one(
                # Match on unique description
                {
                    "description": problem["description"], 
                    "key": problem["key"],
                    "jira_source": config["issue-extractor"]["jira_source"],
                    "project_id": projectId
                },
                {"$set": problem},  # Update with the full problem document
                upsert=True  # Insert if not found
            )
        logging.info(f"Standardized problems {row['key']} saved or updated in MongoDB collection: {
                     config['mongodb']['processed_collection']}")
    return standardized_problems

def main_execution_flow(projectId, stage):

    try:
        load_dotenv()
        # Load configuration
        config = load_configuration(projectId)

        # Setup LLM and embeddings
        llm = setup_llm(config)
        embeddings = setup_embeddings(config)

        # Connect to MongoDB
        db = connect_to_mongo(
            config["mongodb"]["uri"], config["mongodb"]["database"])
        raw_data = load_collection(
            db, 
            config["mongodb"]["raw_collection"], 
            query={
                'jira_source': config["issue-extractor"]["jira_source"],
                'project_id': projectId})

        if stage == 1:
            logging.info("Starting stage 1")

            # Preprocess and create vector store
            cleaned_data = clean_data(raw_data)
            vector_store = create_vector_store(cleaned_data, embeddings)

            # Process documents and extract problems
            standardized_problems = process_and_store_problems(
                cleaned_data, vector_store, llm, config, db, projectId)

        if stage <= 2:
            # Load MongoDb Documents that were created in a previous code block to load all documents that exists in the collection
            standardized_problems = load_collection(
                db, 
                config["mongodb"]["processed_collection"], 
                query={"jira_source": config["issue-extractor"]["jira_source"],
                       "project_id": projectId})
            
            logging.info(f"Number of Loaded Documents: {
                         len(standardized_problems)}")

            # Ensure standardized problems are strings for embedding
            standardized_problem_rows = standardized_problems[[
                'description', 'problem_type', 'key']].to_dict(orient='records')

            # Extract just the descriptions as strings for embedding
            descriptions_only = [item["description"]
                                 for item in standardized_problem_rows]

            # Generate embeddings for the descriptions
            problem_embeddings = embeddings.embed_documents(descriptions_only)

            # Assess optimal number of clusters
            optimal_n_clusters = assess_optimal_n_clusters(
                embeddings=problem_embeddings,
                max_clusters=config["clustering"]["max_clusters"]
            )

            # Perform semantic clustering on the dictionaries
            clustered_problems = semantic_clustering(
                problem_rows=standardized_problem_rows,
                embeddings=problem_embeddings,
                n_clusters=optimal_n_clusters
            )
            # Preprocess clustered problems
            clustered_problems_df = preprocess_clustered_problems(
                clustered_problems)

            # Analysis and reporting
            frequency = problem_frequency_analysis(clustered_problems_df)

            # Generate cluster summary report
            summaries = generate_cluster_summary(clustered_problems, llm, config)

            # Save report in HTML format

            generate_enhanced_report(
                frequency,
                summaries,
                projectId=projectId
            )

        logging.info(f"Analysis completed for project: {projectId}")

        return True

    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise
