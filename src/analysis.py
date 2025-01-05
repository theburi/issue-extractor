from src.llm_utils import parse_llm_output, setup_llm
from langchain_core.prompts import PromptTemplate 
import pandas as pd
from collections import Counter
import logging

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
    if "problem_types" not in data.columns:
        raise ValueError("DataFrame must contain a 'problem_types' column")
    
    logging.info("Starting problem frequency analysis.")
    problem_list = data["problem_types"].explode()  # Flatten list of problems into rows
    problem_counts = Counter(problem_list)
    frequency_df = pd.DataFrame(problem_counts.items(), columns=["problem_types", "frequency"])
    frequency_df.sort_values(by="frequency", ascending=False, inplace=True)
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
