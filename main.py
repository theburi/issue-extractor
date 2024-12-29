import yaml
import logging
from pathlib import Path
from typing import List, Dict

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

def main():
    try:
        # Load configuration
        config_path = Path("./config/config.yaml")
        config = load_config(config_path)
        logging.info("Configuration loaded successfully")

        taxonomy = load_config(Path(config["paths"]["taxonomy"]))

        # Setup LLM and embeddings        
        llm = setup_llm(config)
        embeddings = setup_embeddings(config)

        # Connect to MongoDB
        db = connect_to_mongo(config["mongodb"]["uri"], config["mongodb"]["database"])
        raw_data = load_collection(db, config["mongodb"]["raw_collection"])
        
        # Preprocess and create vector store
        cleaned_data = clean_data(raw_data)
        vector_store = create_vector_store(cleaned_data, embeddings)
        
        # Process documents and extract problems
        problems = []
        standardized_problems=[]
        for _, row in cleaned_data.iterrows():
            try:
                similar_docs = vector_store.similarity_search(
                    row['communication'],
                    k=3
                )
                
                # Format similar cases
                similar_cases = "\n".join([d.page_content for d in similar_docs])
                
                # Create chain with updated prompt variables
                prompt = PromptTemplate(
                    template=config["prompts"]["problem_extraction"],
                    input_variables=["text", "similar_cases"]
                )
                
                chain = prompt | llm
                results = chain.invoke({
                    "text": row['communication'],
                    "similar_cases": similar_cases
                })
                for result in parse_llm_output(results):                   
                    problems.append(result)
                    standardized_problem = standardize_problems(result, taxonomy=taxonomy)
                    standardized_problems.append(standardized_problem)
                    
            except Exception as e:
                logging.error(f"Error processing document: {str(e)}", exc_info=True)
                continue
        
         # Ensure standardized problems are strings for embedding
        standardized_problem_texts = [p["description"] for p in standardized_problems if p and "description" in p]

        # Semantic clustering of problems
        problem_embeddings = embeddings.embed_documents(standardized_problem_texts)
        clustered_problems = semantic_clustering(
            standardized_problem_texts,
            problem_embeddings
        )
        
        # Analysis and reporting
        print(clustered_problems)
        frequency = problem_frequency_analysis(clustered_problems)
        # problem_customer_map = map_problems_to_customers(clustered_problems)
        
        # Generate enhanced HTML report
        output_path = Path("./data/results/problem_report.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generate_enhanced_report(
            frequency,
            # problem_customer_map,
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