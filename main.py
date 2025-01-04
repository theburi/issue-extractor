import yaml
import logging
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
import argparse  # Added for command-line argument parsing

from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate   
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama.llms import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.db.mongodb_client import connect_to_mongo, load_collection, insert_to_collection
from src.preprocessing import clean_data
from src.problem_extraction import parse_llm_output, standardize_problems
from src.analysis import problem_frequency_analysis
from src.reporting import generate_enhanced_report, generate_problem_report
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


def setup_llm(config: Dict) -> OllamaLLM:
    return OllamaLLM(
        model=config["llm"]["model_name"],
        temperature=config["llm"]["temperature"]
    )

def setup_embeddings(config: Dict) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=config["embeddings"]["model_name"]
    )


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

def semantic_clustering(problems: List[str], embeddings: List[np.ndarray], n_clusters: int = 5) -> Dict[int, List[str]]:
    """Cluster problems based on their semantic embeddings."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)
    
    clustered_problems = {i: [] for i in range(n_clusters)}
    for problem, cluster_id in zip(problems, clusters):
        clustered_problems[cluster_id].append(problem)
    
    return clustered_problems

def preprocess_clustered_problems(clustered_problems: Dict[int, List[str]]) -> pd.DataFrame:
    """Preprocess clustered problems into a DataFrame with counts."""
    processed_data = []
    
    for cluster_id, problems in clustered_problems.items():
        problem_counts = pd.Series(problems).value_counts().to_dict()  # Count occurrences
        for problem, count in problem_counts.items():
            processed_data.append({
                "cluster_id": cluster_id,
                "problem_types": problem,
                "frequency": count
            })
    
    return pd.DataFrame(processed_data)

def process_row(row, vector_store, llm, taxonomy, config, db):
    """Process a single row of data."""
    try:
        # Check if the record already exists
        existing_record = db[config["mongodb"]["processed_collection"]].find_one(
            {"key": row["key"], "version": config["prompts"]["version"], "problem_type": { "$ne": "unknown" } }
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
        standardized_results = [standardize_problems(result, taxonomy, llm, config["prompts"]["problem_type"]) for result in parse_llm_output(results)]
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
        raw_data = load_collection(db, config["mongodb"]["raw_collection"])

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
            logging.info(f"Standardized Problems: { type(standardized_problems) }")
            
            # Ensure standardized problems are strings for embedding
            standardized_problem_texts = standardized_problems['description'].tolist()

            # Semantic clustering of problems
            problem_embeddings = embeddings.embed_documents(standardized_problem_texts)
            clustered_problems = semantic_clustering(
                standardized_problem_texts,
                problem_embeddings
            )
            
            # Preprocess clustered problems
            clustered_problems_df = preprocess_clustered_problems(clustered_problems)
                     
            # Analysis and reporting
            frequency = problem_frequency_analysis(clustered_problems_df)
            
            # Generate enhanced HTML report
            output_path = Path("./data/results/problem_report.html")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            generate_enhanced_report(
                frequency,
                # vector_store,
                output_path=str(output_path)
            )
            
            logging.info(f"Analysis complete - Report available at {output_path}")
            return True
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise



if __name__ == "__main__":
    main()