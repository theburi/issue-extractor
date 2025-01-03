import pandas as pd
from collections import Counter
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


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
