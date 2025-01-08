from src.llm_utils import parse_llm_output, setup_llm
from langchain_core.prompts import PromptTemplate 
import pandas as pd
from collections import Counter
import logging
from typing import List, Dict

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
    summaries = {}


    llm = setup_llm(config, max_tokens=200)


    for cluster_id, problems in clustered_problems.items():
        descriptions = "\n".join([problem["description"] for problem in problems])
        print("Number of problems in cluster", cluster_id, ":", len(problems))
        try:
            prompt = PromptTemplate(
                template=config["prompts"]["generate_cluster_summary"],
                input_variables=["descriptions"]
                )
            chain = prompt | llm
            results = chain.invoke({
                "descriptions": descriptions
                })
            summaries[cluster_id] = results.strip()
            logging.info(f"Summary for cluster {cluster_id}: {results.strip()}")
        except Exception as e:
            logging.error(f"Failed to generate summary for cluster {cluster_id}: {e}")
            summaries[cluster_id] = "Error in generating summary."



    logging.info("Cluster summaries generated successfully.")
    return summaries