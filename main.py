import yaml
import logging
from pathlib import Path
from typing import List, Dict

from langchain import LLMChain, PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.db.mongodb_client import connect_to_mongo, load_collection, insert_to_collection
from src.preprocessing import clean_data
from src.problem_extraction import extract_problems, standardize_problems
from src.analysis import problem_frequency_analysis, map_problems_to_customers
from src.reporting import generate_enhanced_report, generate_problem_report
from sklearn.cluster import KMeans
import numpy as np


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        raise
def setup_llm_and_embeddings(config: Dict):
    """Initialize LLM and embeddings."""
    llm = ChatOpenAI(
        model_name=config["llm"]["model_name"],
        temperature=config["llm"]["temperature"]
    )
    embeddings = OpenAIEmbeddings()
    return llm, embeddings

def create_vector_store(documents: List, embeddings) -> Chroma:
    """Create and populate vector store."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)
    
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

def main():
    try:
        # Load configuration
        config_path = Path("./config/config.yaml")
        config = load_config(config_path)
        logging.info("Configuration loaded successfully")

        # Setup LLM and embeddings
        llm, embeddings = setup_llm_and_embeddings(config)
        
        # Connect to MongoDB
        db = connect_to_mongo(config["mongodb"]["uri"], config["mongodb"]["database"])
        raw_data = load_collection(db, config["mongodb"]["raw_collection"])
        
        # Preprocess and create vector store
        cleaned_data = clean_data(raw_data)
        vector_store = create_vector_store(cleaned_data, embeddings)
        
        # Enhanced problem extraction with RAG
        problems = []
        for doc in cleaned_data:
            # Find similar cases
            similar_docs = vector_store.similarity_search(
                doc["communication"],
                k=3
            )
            
            # Create enhanced context
            context = {
                "current_doc": doc["communication"],
                "similar_cases": [d.page_content for d in similar_docs]
            }
            
            # Extract problems using LLM
            prompt = PromptTemplate(
                template=config["prompts"]["problem_extraction"],
                input_variables=["context"]
            )
            
            chain = LLMChain(llm=llm, prompt=prompt)
            result = chain.run(context=context)
            problems.extend(result["problems"])
        
        # Standardize and analyze problems
        taxonomy = load_config(Path(config["paths"]["taxonomy"]))
        standardized_problems = [
            standardize_problems(p, taxonomy=taxonomy)
            for p in problems
        ]
        
        # Semantic clustering of problems
        problem_embeddings = embeddings.embed_documents(standardized_problems)
        clustered_problems = semantic_clustering(
            standardized_problems,
            problem_embeddings
        )
        
        # Analysis and reporting
        frequency = problem_frequency_analysis(clustered_problems)
        problem_customer_map = map_problems_to_customers(clustered_problems)
        
        # Generate enhanced HTML report
        output_path = Path("./data/results/problem_report.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generate_enhanced_report(
            frequency,
            problem_customer_map,
            vector_store,
            str(output_path)
        )
        
        logging.info(f"Analysis complete - Report available at {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()