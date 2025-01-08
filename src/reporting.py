import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from typing import Dict, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def generate_problem_report(frequency_data: pd.DataFrame, output_path: str):
    """
    Generates a CSV report of the most common problems.
    
    Args:
        frequency_data (pd.DataFrame): DataFrame with problem frequencies.
        output_path (str): Path to save the report.
    """
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    logging.info("Generating problem frequency report.")
    frequency_data.to_csv(output_path, index=False)
    logging.info(f"Problem frequency report saved at {output_path}.")


def visualize_problem_frequencies(frequency_data: pd.DataFrame, output_path: str):
    """
    Creates a bar chart of the most common problems and saves it as an image.
    
    Args:
        frequency_data (pd.DataFrame): DataFrame with problem frequencies.
        output_path (str): Path to save the visualization.
    """
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    logging.info("Generating bar chart for problem frequencies.")
    plt.figure(figsize=(10, 6))
    plt.bar(frequency_data["problem"], frequency_data["frequency"])
    plt.xticks(rotation=45, ha="right")
    plt.title("Most Common Problems Reported")
    plt.xlabel("Problem")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Bar chart saved at {output_path}.")


def visualize_trends(trend_data: pd.DataFrame, output_path: str):
    """
    Creates a line chart showing problem trends over time and saves it as an image.
    
    Args:
        trend_data (pd.DataFrame): DataFrame with problem trends over time.
        output_path (str): Path to save the visualization.
    """
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    logging.info("Generating line chart for problem trends.")
    plt.figure(figsize=(12, 6))
    for problem in trend_data["problems"].unique():
        problem_data = trend_data[trend_data["problems"] == problem]
        plt.plot(problem_data["date"], problem_data["frequency"], label=problem)

    plt.title("Problem Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Frequency")
    plt.legend(title="Problems", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Line chart saved at {output_path}.")

def generate_enhanced_report(
    frequency_data: Dict,
    # problem_customer_map: Dict,
    output_path: str
) -> None:
    """Generate enhanced HTML report with problem analysis."""
    
    # Create report data
    report_data = {
        "problem_frequency": pd.DataFrame(frequency_data).to_html(),
        # "cluster_id": pd.DataFrame(problem_customer_map).to_html(),
        "total_problems": len(frequency_data),
        # "total_customers": len(set(problem_customer_map.values()))
    }
    
    # Load template
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")
    
    # Generate HTML
    html_content = template.render(data=report_data)
    
    # Save report
    output_file = Path(output_path)
    output_file.write_text(html_content)
