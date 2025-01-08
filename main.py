import yaml
import logging
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
import argparse  # Added for command-line argument parsing

from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate   
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.db.mongodb_client import connect_to_mongo, load_collection, insert_to_collection
from src.preprocessing import clean_data
from src.problem_extraction import standardize_problems
from src.analysis import problem_frequency_analysis, generate_cluster_summary
from src.reporting import generate_enhanced_report, generate_problem_report
from src.llm_utils import parse_llm_output, setup_llm, setup_embeddings
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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




def create_vector_store(documents: List, embeddings) -> Chroma:
    # Convert each string document into a Document object
    document_objects = [Document(page_content=doc) for doc in documents]
    
    """Create and populate vector store."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(document_objects)
    
    return Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./data/vectorstore"
    )

def semantic_clustering(
    problem_rows: List[Dict[str, str]],
    embeddings: List[np.ndarray],
    n_clusters: int = 5
) -> Dict[int, List[Dict[str, str]]]:
    """Cluster problems based on their semantic embeddings."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)
    
    # Create a dictionary for each cluster
    clustered_problems = {i: [] for i in range(n_clusters)}
    
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


def process_row(row, vector_store, llm, taxonomy, config, db):
    """Process a single row of data."""
    try:
        # Check if the record already exists

        existing_record = db[config["mongodb"]["processed_collection"]].find_one(
            {
                "key": row["key"]
                , "version": config["prompts"]["version"]
                , "problem_type": { "$ne": "unknown" }                
            }
        )
        if existing_record:
            logging.info(f"Record with key {row['key']} and version {config['prompts']['version']} already exists. Skipping processing.")
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
        standardized_results = [standardize_problems(result, taxonomy) for result in parse_llm_output(results)]
        for result in standardized_results:
            result["customer_id"] = row["cid"]
            result["key"] = row["key"]
            result["version"] = config["prompts"]["version"]
        return standardized_results
    except Exception as e:
        logging.error(f"Error processing row: {e}", exc_info=True)
        return []

def main():
    parser = argparse.ArgumentParser(description="Issue Extractor")
    parser.add_argument('--stage', type=int, required=True, help='Stage number of the pipeline (e.g., 1, 2, 3)')
    args = parser.parse_args()

    try:
        logging.info("Starting stage 1")
        load_dotenv()
        # Load configuration
        config = load_configuration()

        # Setup LLM and embeddings        
        llm = setup_llm(config)
        embeddings = setup_embeddings(config)

        # Connect to MongoDB
        db = connect_to_mongo(config["mongodb"]["uri"], config["mongodb"]["database"])
        raw_data = load_collection(db, config["mongodb"]["raw_collection"], query= {'jira_source': 'text ~ backup and project = Support'})

        if args.stage == 1:            
            # Preprocess and create vector store
            cleaned_data = clean_data(raw_data)
            vector_store = create_vector_store(cleaned_data, embeddings)
            
            # Process documents and extract problems
            standardized_problems = []
            for _, row in cleaned_data.iterrows():
                problems = process_row(row, vector_store, llm, config["taxonomy"], config, db)            
                for problem in problems:
                    standardized_problems.extend(problem)                    
                    db[config["mongodb"]["processed_collection"]].update_one(
                            {"description": problem["description"], "key": problem["key"]},  # Match on unique description
                            {"$set": problem},  # Update with the full problem document
                            upsert=True  # Insert if not found
                        )
                logging.info(f"Standardized problems {row['key']} saved or updated in MongoDB collection: {config['mongodb']['processed_collection']}")
               

        if args.stage <= 2:        
            # Load MongoDb Documents that were created in a previous code block to load all documents that exists in the collection
            standardized_problems = load_collection(db, config["mongodb"]["processed_collection"])
            logging.info(f"Number of Loaded Documents: { len(standardized_problems) }")
            
            # Ensure standardized problems are strings for embedding
            standardized_problem_rows = standardized_problems[['description', 'problem_type']].to_dict(orient='records')

            # Extract just the descriptions as strings for embedding
            descriptions_only = [item["description"] for item in standardized_problem_rows]

            # Generate embeddings for the descriptions
            problem_embeddings = embeddings.embed_documents(descriptions_only)
            # Perform semantic clustering on the dictionaries
            clustered_problems = semantic_clustering(
                problem_rows=standardized_problem_rows,
                embeddings=problem_embeddings,
                n_clusters=config["clustering"]["n_clusters"]
            )
            # Preprocess clustered problems
            clustered_problems_df = preprocess_clustered_problems(clustered_problems)
                
            # Analysis and reporting
            frequency = problem_frequency_analysis(clustered_problems_df)
            
            # Generate cluster summary report
            summaries = generate_cluster_summary(clustered_problems, llm, config)
            # Convert summaries to a DataFrame for reporting or saving
            summary_df = pd.DataFrame.from_dict(summaries, orient='index', columns=['summary'])
            # Save report in HTML format
            summary_output_path = Path("./data/results/cluster_summaries.html")
            summary_output_path.parent.mkdir(parents=True, exist_ok=True)
            summary_df.to_html(summary_output_path)

        logging.info(f"Cluster summaries saved at {summary_output_path}")

        # Generate enhanced HTML report
        output_path = Path("./data/results/problem_report.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generate_enhanced_report(
            frequency,
            # vector_store,
            output_path=str(output_path)
        )
        
        logging.info(f"Analysis complete - Report available at {output_path}")
        
        # from sklearn.decomposition import PCA
        # import matplotlib.pyplot as plt

        # pca = PCA(n_components=2)
        # reduced_embeddings = pca.fit_transform(problem_embeddings)
        # # Each point in 'reduced_embeddings' gets a color based on its cluster label
        # plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], c="blue")
        # plt.show()

        return True
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise



if __name__ == "__main__":
    main()